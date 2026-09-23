from collections import defaultdict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.models import AssetQuote

class ReportRenderer:
    def __init__(self, template_dir: str = "src/templates"):
        self.env = Environment(loader=FileSystemLoader(Path(template_dir)))
        self.template = self.env.get_template("report.html.j2")

    def render(self, quotes: list[AssetQuote], report_type: str, date_str: str) -> str:
        grouped = defaultdict(list)
        up_count = sum(1 for q in quotes if q.color == "up")
        down_count = sum(1 for q in quotes if q.color == "down")
        flat_count = sum(1 for q in quotes if q.color == "flat")

        for q in quotes:
            grouped[q.category].append(q)

        if report_type == "morning":
            title = f"【全球财经晨报】隔夜欧美大宗复盘与外盘盘点 ({date_str})"
        else:
            title = f"【全球财经晚报】亚太核心股指收盘与欧洲盘初盘点 ({date_str})"

        return self.template.render(
            title=title,
            date_str=date_str,
            grouped_quotes=grouped,
            total_count=len(quotes),
            up_count=up_count,
            down_count=down_count,
            flat_count=flat_count
        )
