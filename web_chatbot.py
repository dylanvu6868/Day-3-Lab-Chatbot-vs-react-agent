import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.agent.agent import ReActAgent
from src.core.provider_factory import build_provider
from src.database.sqlite_school_db import ensure_bootstrap
from src.tools.school_db_tools import get_tools


ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def build_agent() -> ReActAgent:
    os.environ.setdefault("DEFAULT_PROVIDER", os.getenv("WEB_PROVIDER", "openai"))
    os.environ.setdefault("DEFAULT_MODEL", os.getenv("WEB_MODEL", "gpt-4o-mini"))
    os.environ.setdefault("LOG_TO_CONSOLE", "false")
    ensure_bootstrap()
    return ReActAgent(llm=build_provider(), tools=get_tools(), max_steps=5)


def summarize_trace(trace: list[dict[str, Any]]) -> list[dict[str, str]]:
    items = []
    for item in trace:
        output = str(item.get("llm_output", ""))
        action = ReActAgent._extract_action(ChatbotServer.agent, output)
        final = ReActAgent._extract_final_answer(ChatbotServer.agent, output)
        if action:
            tool_name, args = action
            summary = f"Chọn tool {tool_name} với tham số {args or '{}'}"
            phase = "Tool call"
        elif final:
            summary = "Tổng hợp observation và tạo câu trả lời cuối."
            phase = "Final"
        else:
            summary = "Đang phân tích yêu cầu và quyết định bước tiếp theo."
            phase = "Thinking"
        items.append(
            {
                "step": str(item.get("step", "")),
                "phase": phase,
                "summary": summary,
            }
        )
    return items


class ChatbotServer(BaseHTTPRequestHandler):
    agent = build_agent()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", ""}:
            self._send_static(FRONTEND_DIR / "index.html")
            return

        static_path = (FRONTEND_DIR / parsed.path.lstrip("/")).resolve()
        if not self._is_safe_static_path(static_path):
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_static(static_path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/chat":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                self._send_json({"error": "Message is required"}, status=HTTPStatus.BAD_REQUEST)
                return

            previous_history_len = len(self.agent.history)
            answer = self.agent.run(message)
            trace = self.agent.history[previous_history_len:]
            self._send_json(
                {
                    "answer": answer,
                    "trace": summarize_trace(trace),
                    "provider": f"{self.agent.llm.model_name} ({self.agent.llm.__class__.__name__})",
                }
            )
        except Exception as exc:
            self._send_json(
                {"error": f"Server error: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _is_safe_static_path(self, path: Path) -> bool:
        try:
            path.relative_to(FRONTEND_DIR.resolve())
        except ValueError:
            return False
        return path.exists() and path.is_file()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the school chatbot web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ChatbotServer)
    print(f"School Chatbot UI: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
