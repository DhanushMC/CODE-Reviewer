import torch
import torch.nn as nn
from transformers import RobertaTokenizer, RobertaModel
from typing import Dict, Tuple
import re
from app.config import settings
from app.schemas.models import VulnerabilityType, Severity, SupportedLanguage


class VulnerabilityClassifier(nn.Module):
    """CodeBERT-based vulnerability classifier"""
    
    def __init__(self, num_classes=8):
        super().__init__()
        self.codebert = RobertaModel.from_pretrained(settings.codebert_model)
        self.classifier = nn.Linear(self.codebert.config.hidden_size, num_classes)
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, input_ids, attention_mask):
        outputs = self.codebert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits


class VulnerabilityDetector:
    """ML-based vulnerability detection using CodeBERT"""
    
    def __init__(self):
        self.tokenizer = RobertaTokenizer.from_pretrained(settings.codebert_model)
        self.model = VulnerabilityClassifier()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        self.vuln_types = [
            VulnerabilityType.SQL_INJECTION,
            VulnerabilityType.XSS,
            VulnerabilityType.COMMAND_INJECTION,
            VulnerabilityType.PATH_TRAVERSAL,
            VulnerabilityType.HARDCODED_SECRETS,
            VulnerabilityType.WEAK_CRYPTO,
            VulnerabilityType.XXE,
            VulnerabilityType.SAFE,
        ]
        
        # Rule-based patterns for refinement
        self.patterns = {
            VulnerabilityType.SQL_INJECTION: [
                r'execute\s*\(',
                r'cursor\.execute',
                r'query\s*=.*\+.*input',
                r'SELECT.*\+',
                r'INSERT.*\+',
                r'f"SELECT',
                r'f"INSERT',
                r'"SELECT.*\{',
            ],
            VulnerabilityType.XSS: [
                r'innerHTML\s*=',
                r'outerHTML\s*=',
                r'document\.write',
                r'eval\s*\(',
                r'dangerouslySetInnerHTML',
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                r'os\.system',
                r'subprocess\.call',
                r'exec\s*\(',
                r'shell\s*=\s*True',
                r'Runtime\.getRuntime\(\)\.exec',
            ],
            VulnerabilityType.PATH_TRAVERSAL: [
                r'open\s*\(.*input',
                r'File\s*\(.*input',
                r'\.\./\.\./',
                r'path.*\+.*input',
            ],
            VulnerabilityType.HARDCODED_SECRETS: [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ],
            VulnerabilityType.WEAK_CRYPTO: [
                r'md5\(',
                r'sha1\(',
                r'DES\(',
                r'Random\(\)',
                r'Math\.random',
            ],
            VulnerabilityType.XXE: [
                r'XMLReader',
                r'DocumentBuilder',
                r'SAXParser',
                r'setFeature.*external-general-entities',
            ],
        }
    
    def detect(self, code: str, language: SupportedLanguage) -> Dict:
        """
        Detect vulnerabilities in code.
        Uses rule-based detection first (reliable), then ML as a secondary signal.
        """
        # Rule-based detection — this is the primary reliable signal
        # (since CodeBERT here is NOT fine-tuned on vulnerability data,
        #  its raw predictions are essentially random — rules dominate)
        rule_scores = self._apply_rules(code)
        max_rule_vuln = max(rule_scores.items(), key=lambda x: x[1])

        # Only run ML if rules are weak — saves memory when rules are decisive
        if max_rule_vuln[1] >= 0.4:
            # Rules found something — trust them
            final_vuln_type = max_rule_vuln[0]
            final_confidence = min(max_rule_vuln[1] + 0.2, 0.95)
        else:
            # BUG FIX: the original code always ran ML and blindly trusted it,
            # but since the model is NOT fine-tuned it outputs random class predictions
            # with ~12% confidence each. We now fall back to SAFE when rules are weak.
            # To actually use ML, load fine-tuned weights in production.
            try:
                inputs = self.tokenizer(
                    code,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    logits = self.model(**inputs)
                    probs = torch.softmax(logits, dim=-1)
                    ml_confidence, ml_pred_idx = torch.max(probs, dim=-1)
                    ml_confidence = ml_confidence.item()
                    ml_pred = self.vuln_types[ml_pred_idx.item()]
                
                # BUG FIX: un-fine-tuned model produces low confidence (~0.12-0.15)
                # Only trust ML if confidence is above a meaningful threshold
                if ml_confidence > 0.5 and ml_pred != VulnerabilityType.SAFE:
                    final_vuln_type = ml_pred
                    final_confidence = ml_confidence
                else:
                    final_vuln_type = VulnerabilityType.SAFE
                    final_confidence = 1.0 - max_rule_vuln[1]
            except Exception as e:
                print(f"ML model error: {e}")
                final_vuln_type = VulnerabilityType.SAFE
                final_confidence = 0.95
        
        evidence, line_numbers = self._extract_evidence(code, final_vuln_type)
        severity = self._determine_severity(final_vuln_type, final_confidence)
        is_vulnerable = final_vuln_type != VulnerabilityType.SAFE
        
        return {
            "is_vulnerable": is_vulnerable,
            "vulnerability_type": final_vuln_type,
            "severity": severity if is_vulnerable else None,
            "confidence": final_confidence,
            "evidence": evidence,
            "line_numbers": line_numbers,
        }
    
    def _apply_rules(self, code: str) -> Dict[VulnerabilityType, float]:
        """Apply rule-based patterns to score vulnerability likelihood"""
        scores = {}
        for vuln_type, patterns in self.patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    score += 0.2 * len(matches)
            scores[vuln_type] = min(score, 1.0)
        return scores
    
    def _extract_evidence(
        self, code: str, vuln_type: VulnerabilityType
    ) -> Tuple[str, list]:
        """Extract evidence snippet and line numbers"""
        if vuln_type == VulnerabilityType.SAFE:
            return "No vulnerability detected", []
        
        lines = code.split('\n')
        evidence_lines = []
        line_numbers = []
        
        patterns = self.patterns.get(vuln_type, [])
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    evidence_lines.append(line.strip())
                    line_numbers.append(i)
                    break
        
        if evidence_lines:
            evidence = " | ".join(evidence_lines[:3])
        else:
            evidence = f"Potential {vuln_type.value} detected by ML model"
        
        return evidence, line_numbers[:5]
    
    def _determine_severity(
        self, vuln_type: VulnerabilityType, confidence: float
    ) -> Severity:
        """Determine severity based on vulnerability type and confidence"""
        high_severity_types = [
            VulnerabilityType.SQL_INJECTION,
            VulnerabilityType.COMMAND_INJECTION,
            VulnerabilityType.XXE,
        ]
        
        medium_severity_types = [
            VulnerabilityType.XSS,
            VulnerabilityType.PATH_TRAVERSAL,
            VulnerabilityType.HARDCODED_SECRETS,
        ]
        
        if vuln_type in high_severity_types:
            return Severity.HIGH if confidence > 0.7 else Severity.MEDIUM
        elif vuln_type in medium_severity_types:
            return Severity.MEDIUM if confidence > 0.6 else Severity.LOW
        else:
            return Severity.LOW


# Global detector instance (lazy loaded)
_detector = None

def get_detector() -> VulnerabilityDetector:
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = VulnerabilityDetector()
    return _detector
