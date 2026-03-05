@echo off
cd /d "c:\Users\tked1\py\office_mcp_server"
echo IPO情報を取得中...
uv run scrape_ipo_perfect.py
echo 完了しました。
pause
