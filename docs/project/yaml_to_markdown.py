#!/usr/bin/env python3
"""
Convert docs/source/*.md (YAML frontmatter + notes) into human-readable Markdown.

Usage:
    python docs/yaml_to_markdown.py
    python docs/yaml_to_markdown.py --input docs/source --output docs/generated
    python docs/yaml_to_markdown.py --watch   # not implemented; single run only

Requires: PyYAML  (pip install pyyaml)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (yaml_data, markdown_body_after_frontmatter)."""
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter: missing closing ---")

    data = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return data if isinstance(data, dict) else {}, body


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------


def h1(title: str) -> str:
    return f"# {title}\n\n"


def h2(title: str) -> str:
    return f"## {title}\n\n"


def h3(title: str) -> str:
    return f"### {title}\n\n"


def bullets(items: list[Any]) -> str:
    if not items:
        return "_None_\n\n"
    lines = []
    for item in items:
        if isinstance(item, dict):
            if "title" in item and "description" in item:
                lines.append(f"- **{item['title']}** — {item['description']}")
            else:
                lines.append(f"- {_format_inline_dict(item)}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n\n"


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No data_\n\n"
    sep = "| " + " | ".join(headers) + " |\n"
    sep += "| " + " | ".join("---" for _ in headers) + " |\n"
    for row in rows:
        sep += "| " + " | ".join(str(c).replace("\n", " ") for c in row) + " |\n"
    return sep + "\n"


def json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False) + "\n```\n\n"


def code_block(code: str, language: str = "") -> str:
    lang = language or ""
    return f"```{lang}\n{code.rstrip()}\n```\n\n"


def key_value_table(data: dict[str, Any], skip: set[str] | None = None) -> str:
    skip = skip or set()
    rows = []
    for key, value in data.items():
        if key in skip:
            continue
        if isinstance(value, (dict, list)):
            continue
        rows.append([_label(key), str(value)])
    return table(["Field", "Value"], rows) if rows else ""


def _label(key: str) -> str:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", key).replace("_", " ").title()


def _format_inline_dict(d: dict[str, Any]) -> str:
    parts = [f"{_label(k)}: {v}" for k, v in d.items() if v is not None]
    return ", ".join(parts)


def append_body_notes(body: str) -> str:
    if not body:
        return ""
    return h2("Additional notes") + body + "\n\n"


# ---------------------------------------------------------------------------
# Specialized renderers (match docs/source file shapes ≈ schema.ts)
# ---------------------------------------------------------------------------


def render_metadata(data: dict[str, Any], body: str) -> str:
    out = h1(data.get("name", "Project Metadata"))
    out += f"{data.get('description', '')}\n\n"
    out += table(
        ["Field", "Value"],
        [
            ["Project ID", data.get("projectId", "")],
            ["Version", data.get("version", "")],
            ["Language", data.get("language", "")],
            ["Framework", data.get("framework", "")],
            ["Category", data.get("category", "")],
            ["Status", data.get("status", "")],
            ["Featured", "Yes" if data.get("featured") else "No"],
            ["Repository", data.get("repositoryUrl", "")],
            ["Live demo", data.get("liveDemoUrl", "")],
            ["Created", data.get("createdAt", "")],
            ["Updated", data.get("updatedAt", "")],
        ],
    )
    out += h2("Tech stack")
    out += bullets(data.get("techStack", []))
    out += append_body_notes(body)
    return out


def render_overview(data: dict[str, Any], body: str) -> str:
    out = h1("Project Overview")

    ps = data.get("problemStatement", {})
    out += h2(ps.get("problemTitle", "Problem"))
    out += f"{ps.get('problemDescription', '')}\n\n"
    out += h3("Pain points")
    out += bullets(ps.get("problemList", []))

    sol = data.get("solution", {})
    out += h2(sol.get("solutionTitle", "Solution"))
    out += bullets(sol.get("solutionList", []))

    km = data.get("keyMetrics", {})
    out += h2(km.get("metricsTitle", "Key metrics"))
    out += bullets(km.get("metricsList", []))

    links = data.get("links", {})
    if links:
        out += h2("Links")
        out += table(
            ["Resource", "URL"],
            [[k.title(), v] for k, v in links.items()],
        )

    mg = data.get("mediaGallery", {})
    if mg:
        out += h2(mg.get("title", "Media gallery"))
        if mg.get("description"):
            out += f"{mg['description']}\n\n"
        for item in mg.get("items", []):
            out += h3(item.get("title", "Media item"))
            out += f"{item.get('description', '')}\n\n"
            out += f"- **Type:** {item.get('type', '')} | **Category:** {item.get('category', '')}\n"
            out += f"- ![{item.get('alt', '')}]({item.get('url', '')})\n\n"

    media = data.get("mediaItems", [])
    if media:
        out += h2("Additional media")
        for item in media:
            out += h3(item.get("title", ""))
            out += f"{item.get('description', '')}\n\n"

    metrics = data.get("metrics", [])
    if metrics:
        out += h2("Metrics")
        out += table(
            ["Label", "Value", "Description"],
            [
                [m.get("label", ""), m.get("value", ""), m.get("description", "")]
                for m in metrics
            ],
        )

    out += append_body_notes(body)
    return out


def render_api_schema(data: dict[str, Any], body: str) -> str:
    out = h1("API Schema")
    out += f"**API type:** {data.get('type', 'REST')}\n\n"

    endpoints = data.get("httpEndpoints", [])
    by_tag: dict[str, list[dict[str, Any]]] = {}
    for ep in endpoints:
        tags = ep.get("tags") or ["general"]
        tag = tags[0] if tags else "general"
        by_tag.setdefault(tag, []).append(ep)

    for tag in sorted(by_tag.keys()):
        out += h2(tag.title())
        for ep in by_tag[tag]:
            method = ep.get("method", "GET")
            path = ep.get("urlPath", "")
            summary = ep.get("summary", ep.get("id", ""))
            out += h3(f"`{method}` {path}")
            out += f"**{summary}**\n\n"
            out += f"{ep.get('description', '')}\n\n"
            auth = "Yes" if ep.get("authenticated") else "No"
            out += f"| | |\n|---|---|\n"
            out += f"| **Auth required** | {auth} |\n"
            out += f"| **Rate limit** | {ep.get('rateLimit', '—')} |\n"
            out += f"| **Tags** | {', '.join(ep.get('tags', []))} |\n\n"

            params = ep.get("parameters") or []
            if params:
                out += h4("Parameters")
                out += table(
                    ["Name", "In", "Type", "Required", "Description"],
                    [
                        [
                            p.get("name", ""),
                            p.get("in", ""),
                            p.get("type", ""),
                            "Yes" if p.get("required") else "No",
                            p.get("description", ""),
                        ]
                        for p in params
                    ],
                )

            req = ep.get("requestBody")
            if req:
                out += h4("Request body")
                out += f"**Content-Type:** `{req.get('contentType', 'application/json')}`\n\n"
                if req.get("schema"):
                    out += "**Schema (summary):**\n\n"
                    out += json_block(req["schema"])
                if req.get("example"):
                    out += "**Example:**\n\n"
                    out += json_block(req["example"])

            responses = ep.get("responses") or []
            if responses:
                out += h4("Responses")
                for resp in responses:
                    status = resp.get("status", "")
                    out += f"- **{status}** — {resp.get('description', '')}\n"
                    if resp.get("example") is not None:
                        out += "\n"
                        out += json_block(resp["example"])

            out += "---\n\n"

    out += append_body_notes(body)
    return out


def h4(title: str) -> str:
    return f"#### {title}\n\n"


def render_features(data: dict[str, Any], body: str) -> str:
    out = h1("Project Features")
    for feat in data.get("features", []):
        title = feat.get("title", feat.get("id", "Feature"))
        out += h2(title)
        out += f"{feat.get('description', '')}\n\n"
        out += table(
            ["Property", "Value"],
            [
                ["ID", feat.get("id", "")],
                ["Category", feat.get("category", "")],
                ["Status", feat.get("status", "")],
                ["Icon", feat.get("icon", "")],
            ],
        )
        if feat.get("highlights"):
            out += h3("Highlights")
            out += bullets(feat["highlights"])
        if feat.get("techStack"):
            out += h3("Tech stack")
            out += bullets(feat["techStack"])
        if feat.get("metrics"):
            out += h3("Metrics")
            out += table(
                ["Label", "Value", "Trend"],
                [
                    [
                        m.get("label", ""),
                        m.get("value", ""),
                        m.get("trend", ""),
                    ]
                    for m in feat["metrics"]
                ],
            )
        snippet = feat.get("codeSnippet")
        if snippet and snippet.get("code"):
            out += h3("Code snippet")
            if snippet.get("filename"):
                out += f"_{snippet['filename']}_\n\n"
            out += code_block(snippet["code"], snippet.get("language", "python"))
    out += append_body_notes(body)
    return out


def render_architecture(data: dict[str, Any], body: str) -> str:
    out = h1("Architecture")

    for layer in data.get("layers", []):
        out += h2(layer.get("name", "Layer"))
        out += f"{layer.get('description', '')}\n\n"
        if layer.get("components"):
            out += h3("Components")
            out += bullets(layer["components"])
        if layer.get("responsibilities"):
            out += h3("Responsibilities")
            out += bullets(layer["responsibilities"])
        if layer.get("technologies"):
            out += h3("Technologies")
            out += bullets(layer["technologies"])

    patterns = data.get("designPatterns", [])
    if patterns:
        out += h2("Design patterns")
        out += table(
            ["Pattern", "Category", "Description"],
            [
                [
                    f"{p.get('emoji', '')} {p.get('title', '')}".strip(),
                    p.get("category", ""),
                    p.get("description", ""),
                ]
                for p in patterns
            ],
        )

    for title, key in [
        ("Scalability strategies", "scalabilityStrategies"),
        ("Security strategies", "securityStrategies"),
    ]:
        items = data.get(key, [])
        if items:
            out += h2(title)
            out += bullets(items)

    cache = data.get("cacheStrategies", [])
    if cache:
        out += h2("Cache strategies")
        out += table(
            ["Name", "TTL", "Coverage", "Description"],
            [
                [
                    c.get("name", ""),
                    c.get("ttl", ""),
                    c.get("coverage", ""),
                    c.get("description", ""),
                ]
                for c in cache
            ],
        )

    af = data.get("architectureFeatures", [])
    if af:
        out += h2("Architecture highlights")
        for f in af:
            out += h3(f"{f.get('emoji', '')} {f.get('title', '')}".strip())
            out += f"{f.get('description', '')}\n\n"

    diagram = data.get("architectureDiagram", {})
    if diagram:
        out += h2("Architecture diagram")
        legend = diagram.get("legendItems", [])
        if legend:
            out += h3("Legend")
            out += table(
                ["Type", "Label"],
                [[item.get("type", ""), item.get("label", "")] for item in legend],
            )
        nodes = diagram.get("nodes", [])
        if nodes:
            out += h3("Nodes")
            out += table(
                ["ID", "Label", "Type", "Status"],
                [
                    [
                        n.get("id", ""),
                        n.get("label", ""),
                        n.get("type", ""),
                        n.get("status", ""),
                    ]
                    for n in nodes
                ],
            )
        conns = diagram.get("connections", [])
        if conns:
            out += h3("Connections")
            out += table(
                ["From", "To", "Label", "Protocol"],
                [
                    [
                        c.get("from", ""),
                        c.get("to", ""),
                        c.get("label", ""),
                        c.get("protocol", ""),
                    ]
                    for c in conns
                ],
            )
        out += h3("Mermaid overview")
        out += _mermaid_from_diagram(diagram)

    df = data.get("dataFlow", {})
    if df:
        out += h2("Data flow")
        for flow_name, label in [
            ("requestFlow", "Request flow"),
            ("eventFlow", "Event flow"),
        ]:
            steps = df.get(flow_name, [])
            if steps:
                out += h3(label)
                for step in sorted(steps, key=lambda s: s.get("number", 0)):
                    out += f"{step.get('number', '')}. **{step.get('title', '')}** — {step.get('description', '')}\n"
                out += "\n"

    td = data.get("techDecisions", {})
    decisions = td.get("decisions", []) if isinstance(td, dict) else []
    if decisions:
        out += h2("Technical decisions")
        for d in decisions:
            out += h3(d.get("title", "Decision"))
            out += f"**Problem:** {d.get('problem', '')}\n\n"
            out += f"**Solution:** {d.get('solution', '')}\n\n"
            out += f"**Outcome:** {d.get('outcome', '')}\n\n"
            if d.get("alternatives"):
                out += h4("Alternatives considered")
                out += bullets(d["alternatives"])

    out += append_body_notes(body)
    return out


def _mermaid_from_diagram(diagram: dict[str, Any]) -> str:
    """Simple flowchart from nodes and connections."""
    lines = ["```mermaid", "flowchart LR"]
    for node in diagram.get("nodes", []):
        nid = node.get("id", "node")
        label = node.get("label", nid).replace('"', "'")
        ntype = node.get("type", "service")
        shape = {
            "client": f"{nid}([{label}])",
            "gateway": f"{nid}{{{label}}}",
            "database": f"{nid}[({label})]",
            "queue": f"{nid}[/{label}/]",
            "monitoring": f"{nid}>{label}]",
        }.get(ntype, f"{nid}[{label}]")
        lines.append(f"    {shape}")
    for conn in diagram.get("connections", []):
        fr, to = conn.get("from", ""), conn.get("to", "")
        lbl = conn.get("label", "")
        if fr and to:
            if lbl:
                lines.append(f'    {fr} -->|{lbl}| {to}')
            else:
                lines.append(f"    {fr} --> {to}")
    lines.append("```\n")
    return "\n".join(lines) + "\n"


def render_infrastructure(data: dict[str, Any], body: str) -> str:
    out = h1("Infrastructure")

    metrics = data.get("metrics", [])
    if metrics:
        out += h2("Metrics")
        out += table(
            ["Label", "Value", "Description"],
            [
                [m.get("label", ""), m.get("value", ""), m.get("description", "")]
                for m in metrics
            ],
        )

    cloud = data.get("cloudServices", [])
    if cloud:
        out += h2("Cloud services")
        out += table(
            ["Service", "Purpose", "Est. cost"],
            [
                [c.get("name", ""), c.get("purpose", ""), c.get("cost", "")]
                for c in cloud
            ],
        )

    layers = data.get("deploymentLayers", [])
    if layers:
        out += h2("Deployment layers")
        for layer in layers:
            out += h3(layer.get("name", "Layer"))
            for comp in layer.get("components", []):
                out += f"- **{comp.get('name', '')}** — {comp.get('description', '')}\n"
            out += "\n"

    docker_files = data.get("dockerFiles", [])
    if docker_files:
        out += h2("Docker configuration")
        for df in docker_files:
            out += h3(df.get("service", "Docker"))
            out += f"{df.get('description', '')}\n\n"
            if df.get("content"):
                out += code_block(df["content"], "yaml")

    out += append_body_notes(body)
    return out


def render_code_showcase(data: dict[str, Any], body: str) -> str:
    out = h1("Code Showcase")
    for ex in data.get("codeExamples", []):
        out += h2(ex.get("title", ex.get("id", "Example")))
        out += f"{ex.get('description', '')}\n\n"
        meta = []
        if ex.get("category"):
            meta.append(f"**Category:** {ex['category']}")
        if ex.get("duration"):
            meta.append(f"**Duration:** {ex['duration']}")
        if ex.get("tags"):
            meta.append(f"**Tags:** {', '.join(ex['tags'])}")
        if meta:
            out += " | ".join(meta) + "\n\n"
        for f in ex.get("files", []):
            out += h3(f.get("name", f.get("path", "File")))
            out += f"**Path:** `{f.get('path', '')}`\n\n"
            if f.get("explanation"):
                out += f"{f['explanation']}\n\n"
            out += code_block(f.get("content", ""), f.get("language", ""))
    out += append_body_notes(body)
    return out


def render_generic(data: dict[str, Any], body: str, title: str) -> str:
    """Fallback: recursive-ish readable structure."""
    out = h1(title)
    out += _render_value(data, depth=2)
    out += append_body_notes(body)
    return out


def _render_value(value: Any, depth: int = 2) -> str:
    prefix = "#" * min(depth, 6)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                parts.append(f"{prefix} {_label(k)}\n\n")
                parts.append(_render_value(v, depth + 1))
            else:
                parts.append(f"- **{_label(k)}:** {v}\n")
        return "\n".join(parts) + "\n\n"
    if isinstance(value, list):
        if value and isinstance(value[0], dict):
            parts = []
            for i, item in enumerate(value, 1):
                parts.append(f"{prefix} Item {i}\n\n")
                parts.append(_render_value(item, depth + 1))
            return "\n".join(parts)
        return bullets(value)
    return f"{value}\n\n"


# Renderer registry: source filename -> renderer
RENDERERS: dict[str, Callable[[dict[str, Any], str], str]] = {
    "ProjectMetadata.md": render_metadata,
    "ProjectOverview.md": render_overview,
    "APISchema.md": render_api_schema,
    "ProjectFeature.md": render_features,
    "ProjectArchitecture.md": render_architecture,
    "ProjectInfrastructure.md": render_infrastructure,
    "ProjectCodeShowCase.md": render_code_showcase,
}


def convert_file(source_path: Path) -> str:
    text = source_path.read_text(encoding="utf-8")
    data, body = split_frontmatter(text)
    name = source_path.name
    title = name.replace(".md", "").replace("_", " ")

    renderer = RENDERERS.get(name)
    if renderer:
        return renderer(data, body)
    return render_generic(data, body, title)


def write_index(output_dir: Path, generated: list[str]) -> None:
    lines = [
        "# Social Events API — Generated documentation",
        "",
        "Auto-generated from `docs/source/` YAML frontmatter.",
        "Regenerate with:",
        "",
        "```bash",
        "python docs/project/yaml_to_markdown.py",
        "```",
        "",
        "## Documents",
        "",
    ]
    for name in sorted(generated):
        stem = Path(name).stem
        lines.append(f"- [{stem}](./{name})")
    lines.append("")
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert docs/source YAML frontmatter to readable Markdown."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "source",
        help="Directory with source .md files (default: docs/source)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "generated",
        help="Output directory (default: docs/generated)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="",
        help="Convert a single file name only (e.g. APISchema.md)",
    )
    args = parser.parse_args()

    input_dir: Path = args.input.resolve()
    output_dir: Path = args.output.resolve()

    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(input_dir.glob("*.md"))
    if args.file:
        sources = [input_dir / args.file]
        if not sources[0].is_file():
            print(f"File not found: {sources[0]}", file=sys.stderr)
            return 1

    generated_names: list[str] = []
    for src in sources:
        try:
            md = convert_file(src)
        except Exception as exc:
            print(f"ERROR {src.name}: {exc}", file=sys.stderr)
            return 1

        out_name = src.stem + ".md"
        out_path = output_dir / out_name
        out_path.write_text(md, encoding="utf-8")
        generated_names.append(out_name)
        print(f"Wrote {out_path}")

    if len(generated_names) > 1:
        write_index(output_dir, generated_names)
        print(f"Wrote {output_dir / 'README.md'}")

    print(f"\nDone — {len(generated_names)} file(s) in {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
