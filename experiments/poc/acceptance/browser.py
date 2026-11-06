"""Independent browser checks inside an offline namespace and disposable profile."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import sys

from playwright.sync_api import sync_playwright


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'")
        super().end_headers()


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory="/work"))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = "http://127.0.0.1:" + str(server.server_port)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
    context = browser.new_context(viewport={"width": 360, "height": 780}, service_workers="block")
    errors = []; foreign = []
    def route(req):
        if req.request.url.startswith(origin + "/"):
            req.continue_()
        else:
            foreign.append("external_request"); req.abort()
    context.route("**/*", route)
    page = context.new_page(); page.on("pageerror", lambda error: errors.append("page_error"))
    if '--preflight' in sys.argv:
        page.set_content('<title>Ensemble browser positive control</title>')
        assert page.title()=='Ensemble browser positive control'
        browser.close();server.shutdown()
        print(json.dumps({'passed':True,'preflight':True}))
        raise SystemExit(0)
    page.goto(origin, wait_until="networkidle")
    board = page.get_by_test_id("board"); board.wait_for(state="visible")
    cells = page.get_by_test_id("cell"); assert cells.count() == 16
    values = lambda: [c.strip() for c in cells.all_text_contents()]
    assert len([v for v in values() if v not in ("", "0")]) == 2
    initial = values()
    for key in ["ArrowLeft", "ArrowUp", "ArrowRight", "ArrowDown"]:
        page.keyboard.press(key)
    assert values() != initial
    for direction in ("left", "right", "up", "down"):
        page.locator('button[data-direction="' + direction + '"]').click()
    assert page.get_by_test_id("score").is_visible()
    assert page.get_by_test_id("status").count() == 1
    page.get_by_test_id("restart").click()
    assert len([v for v in values() if v not in ("", "0")]) == 2
    assert "0" in page.get_by_test_id("score").inner_text()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert not errors, errors
    assert not foreign, foreign
    browser.close()
server.shutdown()
print(json.dumps({"passed": True, "keyboard": True, "touch_buttons": True,
                  "restart": True, "mobile_viewport": True, "external_requests": 0}))
