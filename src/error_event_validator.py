"""
Validation framework for error event parsing and prompt effectiveness.

Tests the error event parser and prompt templates with real failure samples
to verify correctness and effectiveness.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .error_event_schema import ErrorEvent
from .error_event_parser import ErrorEventParser
from .prompt_templates import PromptTemplates


class ErrorEventValidator:
    """Validate error event parsing and prompt generation"""
    
    def __init__(self, output_dir: Path, logger: Optional[logging.Logger] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger("bdf_autotest.validator")
        self.parser = ErrorEventParser(logger=logger)
    
    def validate_event_parsing(self, event: ErrorEvent, expected_fields: List[str]) -> Dict[str, Any]:
        """Validate that an error event has all expected fields"""
        validation_result = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "valid": True,
            "missing_fields": [],
            "field_checks": {},
        }
        
        # Check required fields
        for field in expected_fields:
            value = getattr(event, field, None)
            validation_result["field_checks"][field] = {
                "present": value is not None,
                "non_empty": value is not None and (
                    not isinstance(value, (str, list, dict)) or len(value) > 0
                ),
            }
            
            if not validation_result["field_checks"][field]["present"]:
                validation_result["missing_fields"].append(field)
                validation_result["valid"] = False
        
        return validation_result
    
    def validate_prompt_generation(self, event: ErrorEvent) -> Dict[str, Any]:
        """Validate prompt generation for an event"""
        try:
            prompt = PromptTemplates.get_prompt(event, include_examples=True)
            prompt_no_examples = PromptTemplates.get_prompt(event, include_examples=False)
            
            validation_result = {
                "event_id": event.event_id,
                "valid": True,
                "prompt_length": len(prompt),
                "prompt_length_no_examples": len(prompt_no_examples),
                "contains_examples": len(prompt) > len(prompt_no_examples),
                "contains_error_info": all(
                    keyword in prompt.lower()
                    for keyword in [event.error_type.value, event.message.lower()[:50]]
                ),
            }
            
            # Check prompt quality
            if validation_result["prompt_length"] < 100:
                validation_result["valid"] = False
                validation_result["issue"] = "Prompt too short"
            
            if not validation_result["contains_error_info"]:
                validation_result["valid"] = False
                validation_result["issue"] = "Prompt missing error information"
            
            return validation_result
        except Exception as e:
            return {
                "event_id": event.event_id,
                "valid": False,
                "error": str(e),
            }
    
    def save_event(self, event: ErrorEvent, filename: Optional[str] = None) -> Path:
        """Save error event to JSON file"""
        if filename is None:
            filename = f"error_event_{event.event_id}.json"
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(event.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.logger.debug("Saved error event to %s", output_path)
        return output_path
    
    def save_validation_report(self, validation_results: List[Dict[str, Any]], filename: str = "validation_report.json") -> Path:
        """Save validation results to JSON file"""
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_events": len(validation_results),
            "valid_events": sum(1 for r in validation_results if r.get("valid", False)),
            "results": validation_results,
        }
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info("Saved validation report to %s", output_path)
        return output_path
    
    def run_validation_suite(self, events: List[ErrorEvent]) -> Dict[str, Any]:
        """Run full validation suite on a list of events"""
        self.logger.info("Running validation suite on %d events", len(events))
        
        parsing_results = []
        prompt_results = []
        
        expected_fields = [
            "event_id", "timestamp", "error_type", "severity", "category",
            "message", "context"
        ]
        
        for event in events:
            # Validate parsing
            parsing_result = self.validate_event_parsing(event, expected_fields)
            parsing_results.append(parsing_result)
            
            # Validate prompt generation
            prompt_result = self.validate_prompt_generation(event)
            prompt_results.append(prompt_result)
            
            # Save event
            self.save_event(event)
        
        # Generate summary
        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_events": len(events),
            "parsing": {
                "total": len(parsing_results),
                "valid": sum(1 for r in parsing_results if r.get("valid", False)),
                "invalid": sum(1 for r in parsing_results if not r.get("valid", False)),
            },
            "prompts": {
                "total": len(prompt_results),
                "valid": sum(1 for r in prompt_results if r.get("valid", False)),
                "invalid": sum(1 for r in prompt_results if not r.get("valid", False)),
            },
        }
        
        # Save validation report
        all_results = [
            {
                "event_id": event.event_id,
                "parsing": parsing_results[i],
                "prompt": prompt_results[i],
            }
            for i, event in enumerate(events)
        ]
        self.save_validation_report(all_results)
        
        return summary


def load_validation_samples(samples_dir: Path) -> List[Dict[str, Any]]:
    """Load validation samples from directory"""
    samples = []
    samples_path = Path(samples_dir)
    
    if not samples_path.exists():
        return samples
    
    # Look for JSON files with error event data
    for json_file in samples_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                samples.append(data)
        except Exception as e:
            logging.warning("Failed to load sample %s: %s", json_file, e)
    
    return samples

