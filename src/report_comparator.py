"""
Report comparison module for tracking test trends across runs
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TestComparison:
    """Comparison result for a single test"""
    name: str
    status_before: Optional[str]  # "passed", "failed", or None if not in previous report
    status_after: Optional[str]   # "passed", "failed", or None if not in new report
    change: str  # "new_failure", "fixed", "still_failing", "still_passing", "new_test", "removed"


@dataclass
class ReportComparison:
    """Comparison between two test reports"""
    before_timestamp: str
    after_timestamp: str
    before_summary: Dict[str, int]
    after_summary: Dict[str, int]
    test_comparisons: List[TestComparison]
    summary: Dict[str, int] = field(default_factory=dict)


class ReportComparator:
    """Compare test reports across different runs"""

    def __init__(self, reports_dir: Path = Path("./reports")):
        """
        Initialize report comparator
        
        Args:
            reports_dir: Directory containing JSON reports
        """
        self.reports_dir = Path(reports_dir)

    def load_report(self, report_path: Path) -> Dict[str, Any]:
        """Load a JSON report file"""
        with open(report_path, 'r') as f:
            return json.load(f)

    def get_test_status_map(self, report: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract test name -> status mapping from a report
        
        Returns:
            Dictionary mapping test names to "passed" or "failed"
        """
        status_map = {}
        for test in report.get("tests", []):
            name = test.get("name", "")
            success = test.get("success", False)
            status_map[name] = "passed" if success else "failed"
        return status_map

    def compare_reports(
        self, 
        before_report_path: Path, 
        after_report_path: Path
    ) -> ReportComparison:
        """
        Compare two test reports
        
        Args:
            before_report_path: Path to earlier report
            after_report_path: Path to later report
            
        Returns:
            ReportComparison object with comparison results
        """
        before_report = self.load_report(before_report_path)
        after_report = self.load_report(after_report_path)

        before_timestamp = before_report.get("timestamp", "unknown")
        after_timestamp = after_report.get("timestamp", "unknown")
        before_summary = before_report.get("summary", {})
        after_summary = after_report.get("summary", {})

        before_tests = self.get_test_status_map(before_report)
        after_tests = self.get_test_status_map(after_report)

        # Compare tests
        all_test_names = set(before_tests.keys()) | set(after_tests.keys())
        test_comparisons = []

        for test_name in sorted(all_test_names):
            status_before = before_tests.get(test_name)
            status_after = after_tests.get(test_name)

            if status_before is None and status_after is not None:
                # New test
                change = "new_test"
            elif status_before is not None and status_after is None:
                # Removed test
                change = "removed"
            elif status_before == "passed" and status_after == "failed":
                # New failure (regression)
                change = "new_failure"
            elif status_before == "failed" and status_after == "passed":
                # Fixed test
                change = "fixed"
            elif status_before == "failed" and status_after == "failed":
                # Still failing
                change = "still_failing"
            elif status_before == "passed" and status_after == "passed":
                # Still passing
                change = "still_passing"
            else:
                change = "unknown"

            test_comparisons.append(TestComparison(
                name=test_name,
                status_before=status_before,
                status_after=status_after,
                change=change
            ))

        # Calculate summary statistics
        summary = {
            "new_failures": sum(1 for tc in test_comparisons if tc.change == "new_failure"),
            "fixed": sum(1 for tc in test_comparisons if tc.change == "fixed"),
            "still_failing": sum(1 for tc in test_comparisons if tc.change == "still_failing"),
            "still_passing": sum(1 for tc in test_comparisons if tc.change == "still_passing"),
            "new_tests": sum(1 for tc in test_comparisons if tc.change == "new_test"),
            "removed": sum(1 for tc in test_comparisons if tc.change == "removed"),
        }

        return ReportComparison(
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
            before_summary=before_summary,
            after_summary=after_summary,
            test_comparisons=test_comparisons,
            summary=summary
        )

    def compare_latest_reports(self, n: int = 2) -> Optional[ReportComparison]:
        """
        Compare the N most recent reports
        
        Args:
            n: Number of reports to compare (default: 2, compares latest with previous)
            
        Returns:
            ReportComparison or None if not enough reports exist
        """
        json_reports = sorted(
            self.reports_dir.glob("report_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if len(json_reports) < n:
            return None

        before_path = json_reports[n - 1]  # Previous report
        after_path = json_reports[0]        # Latest report

        return self.compare_reports(before_path, after_path)

    def generate_comparison_report(
        self, 
        comparison: ReportComparison,
        output_path: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Generate HTML and JSON comparison reports
        
        Args:
            comparison: ReportComparison object
            output_path: Optional output path (default: reports/comparison_<timestamp>.html/json)
            
        Returns:
            Dictionary with paths to generated reports
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if output_path is None:
            output_path = self.reports_dir / f"comparison_{timestamp}"
        
        artifacts = {}

        # Generate JSON report
        json_path = output_path.with_suffix(".json")
        json_data = {
            "timestamp": timestamp,
            "before": {
                "timestamp": comparison.before_timestamp,
                "summary": comparison.before_summary,
            },
            "after": {
                "timestamp": comparison.after_timestamp,
                "summary": comparison.after_summary,
            },
            "summary": comparison.summary,
            "tests": [
                {
                    "name": tc.name,
                    "status_before": tc.status_before,
                    "status_after": tc.status_after,
                    "change": tc.change,
                }
                for tc in comparison.test_comparisons
            ]
        }
        json_path.write_text(json.dumps(json_data, indent=2))
        artifacts["json"] = json_path

        # Generate HTML report
        html_path = output_path.with_suffix(".html")
        html_content = self._generate_html_comparison(comparison, timestamp)
        html_path.write_text(html_content)
        artifacts["html"] = html_path

        return artifacts

    def _generate_html_comparison(self, comparison: ReportComparison, timestamp: str) -> str:
        """Generate HTML comparison report"""
        summary = comparison.summary
        
        # Categorize tests by change type
        new_failures = [tc for tc in comparison.test_comparisons if tc.change == "new_failure"]
        fixed = [tc for tc in comparison.test_comparisons if tc.change == "fixed"]
        still_failing = [tc for tc in comparison.test_comparisons if tc.change == "still_failing"]
        new_tests = [tc for tc in comparison.test_comparisons if tc.change == "new_test"]
        removed = [tc for tc in comparison.test_comparisons if tc.change == "removed"]

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Test Report Comparison - {timestamp}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    .success {{ color: #2e7d32; }}
    .failure {{ color: #c62828; }}
    .warning {{ color: #f9a825; }}
    .info {{ color: #1976d2; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background-color: #f5f5f5; }}
    .summary {{ margin-bottom: 2rem; }}
    .summary-item {{ margin: 0.5rem 0; }}
    h2 {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Test Report Comparison</h1>
  <p>Generated: {timestamp}</p>

  <div class="summary">
    <h2>Comparison Summary</h2>
    <div class="summary-item">
      <strong>Before:</strong> {comparison.before_timestamp} 
      (Total: {comparison.before_summary.get('total_tests', 0)}, 
       Passed: {comparison.before_summary.get('passed', 0)}, 
       Failed: {comparison.before_summary.get('failed', 0)})
    </div>
    <div class="summary-item">
      <strong>After:</strong> {comparison.after_timestamp} 
      (Total: {comparison.after_summary.get('total_tests', 0)}, 
       Passed: {comparison.after_summary.get('passed', 0)}, 
       Failed: {comparison.after_summary.get('failed', 0)})
    </div>
  </div>

  <div class="summary">
    <h2>Changes</h2>
    <ul>
      <li class="failure"><strong>New Failures:</strong> {summary.get('new_failures', 0)}</li>
      <li class="success"><strong>Fixed Tests:</strong> {summary.get('fixed', 0)}</li>
      <li class="warning"><strong>Still Failing:</strong> {summary.get('still_failing', 0)}</li>
      <li class="success"><strong>Still Passing:</strong> {summary.get('still_passing', 0)}</li>
      <li class="info"><strong>New Tests:</strong> {summary.get('new_tests', 0)}</li>
      <li class="info"><strong>Removed Tests:</strong> {summary.get('removed', 0)}</li>
    </ul>
  </div>
"""

        # New failures section
        if new_failures:
            html += f"""
  <h2 class="failure">New Failures ({len(new_failures)})</h2>
  <table>
    <thead>
      <tr>
        <th>Test Name</th>
        <th>Previous Status</th>
        <th>Current Status</th>
      </tr>
    </thead>
    <tbody>
"""
            for tc in new_failures:
                html += f"""
      <tr>
        <td>{tc.name}</td>
        <td class="success">{tc.status_before or 'N/A'}</td>
        <td class="failure">{tc.status_after or 'N/A'}</td>
      </tr>
"""
            html += """
    </tbody>
  </table>
"""

        # Fixed tests section
        if fixed:
            html += f"""
  <h2 class="success">Fixed Tests ({len(fixed)})</h2>
  <table>
    <thead>
      <tr>
        <th>Test Name</th>
        <th>Previous Status</th>
        <th>Current Status</th>
      </tr>
    </thead>
    <tbody>
"""
            for tc in fixed:
                html += f"""
      <tr>
        <td>{tc.name}</td>
        <td class="failure">{tc.status_before or 'N/A'}</td>
        <td class="success">{tc.status_after or 'N/A'}</td>
      </tr>
"""
            html += """
    </tbody>
  </table>
"""

        # Still failing section
        if still_failing:
            html += f"""
  <h2 class="warning">Still Failing ({len(still_failing)})</h2>
  <table>
    <thead>
      <tr>
        <th>Test Name</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
"""
            for tc in still_failing:
                html += f"""
      <tr>
        <td>{tc.name}</td>
        <td class="failure">{tc.status_after or 'N/A'}</td>
      </tr>
"""
            html += """
    </tbody>
  </table>
"""

        # New tests section
        if new_tests:
            html += f"""
  <h2 class="info">New Tests ({len(new_tests)})</h2>
  <table>
    <thead>
      <tr>
        <th>Test Name</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
"""
            for tc in new_tests:
                status_class = "success" if tc.status_after == "passed" else "failure"
                html += f"""
      <tr>
        <td>{tc.name}</td>
        <td class="{status_class}">{tc.status_after or 'N/A'}</td>
      </tr>
"""
            html += """
    </tbody>
  </table>
"""

        html += """
</body>
</html>
"""
        return html

