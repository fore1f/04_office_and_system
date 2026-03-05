import asyncio
import win32com.client
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("office-mcp-server")

server = Server("office-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """利用可能なツールの一覧を返します。"""
    return [
        types.Tool(
            name="excel_create_workbook",
            description="新しいExcelブックを作成します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "visible": {"type": "boolean", "description": "Excelを表示するかどうか（デフォルトはTrue）"},
                },
            },
        ),
        types.Tool(
            name="excel_write_cell",
            description="Excelの指定したセルに値を書き込みます（アクティブなシート）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "row": {"type": "integer", "description": "行番号（1から開始）"},
                    "column": {"type": "integer", "description": "列番号（1から開始）"},
                    "value": {"type": "string", "description": "書き込む内容"},
                },
                "required": ["row", "column", "value"],
            },
        ),
        types.Tool(
            name="word_create_document",
            description="新しいWord文書を作成します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "visible": {"type": "boolean", "description": "Wordを表示するかどうか（デフォルトはTrue）"},
                },
            },
        ),
        types.Tool(
            name="word_add_text",
            description="Word文書の末尾にテキストを追加します（アクティブな文書）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "追加するテキスト"},
                },
                "required": ["text"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """ツールの実行をハンドルします。"""
    try:
        if name == "excel_create_workbook":
            visible = arguments.get("visible", True)
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = visible
            excel.Workbooks.Add()
            return [types.TextContent(type="text", text="新しいExcelブックを作成しました。")]

        elif name == "excel_write_cell":
            row = arguments.get("row")
            column = arguments.get("column")
            value = arguments.get("value")
            
            # 既存のExcelインスタンスを取得
            try:
                excel = win32com.client.GetActiveObject("Excel.Application")
                sheet = excel.ActiveSheet
                sheet.Cells(row, column).Value = value
                return [types.TextContent(type="text", text=f"セル({row}, {column})に '{value}' を書き込みました。")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Excelの操作に失敗しました（Excelが開いているか確認してください）: {str(e)}")]

        elif name == "word_create_document":
            visible = arguments.get("visible", True)
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = visible
            word.Documents.Add()
            return [types.TextContent(type="text", text="新しいWord文書を作成しました。")]

        elif name == "word_add_text":
            text = arguments.get("text")
            try:
                word = win32com.client.GetActiveObject("Word.Application")
                doc = word.ActiveDocument
                doc.Content.InsertAfter(text + "\n")
                return [types.TextContent(type="text", text="Word文書にテキストを追加しました。")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Wordの操作に失敗しました（Wordが開いているか確認してください）: {str(e)}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"エラーが発生しました: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="office-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
