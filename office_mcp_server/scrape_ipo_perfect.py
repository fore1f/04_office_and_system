import requests
from bs4 import BeautifulSoup
import win32com.client
import time
import re

def get_ipo_links() -> list[str]:
    url = "https://96ut.com/ipo/schedule.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'kabu.96ut.com/article/ipo/' in href:
                if href not in links:
                    links.append(href)
        return links
    except Exception as e:
        print(f"スケジュール取得エラー: {e}")
        return []

def clean_text(text: str) -> str:
    """不要な改行や連続する空白を削除し、1行にまとめます。"""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def get_detailed_info(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        info = {}
        
        # 1. まず全情報を取得（通常の項目）
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    label = clean_text(th.text)
                    # 幹事関連の項目は後で独自に作成するため、ここではスキップ
                    if '取り扱い証券会社' in label or '引受割合' in label or '幹事団' in label:
                        continue
                    if label not in info:
                        info[label] = clean_text(td.text)

        # 2. 幹事団情報の抽出（証券会社名と枚数のみ、空の改行なし）
        kanji_list = []
        target_h3 = None
        for h3 in soup.find_all('h3'):
            if '取り扱い証券会社' in h3.text:
                target_h3 = h3
                break
        
        if target_h3:
            table = target_h3.find_next('table')
            if table:
                rows = table.find_all('tr')
                if len(rows) > 0:
                    h_row = rows[0].find_all(['td', 'th'])
                    c_name, c_lots = 0, len(h_row) - 1
                    for i, h in enumerate(h_row):
                        t = h.text.strip()
                        if '証券会社' in t: c_name = i
                        elif '枚' in t: c_lots = i
                    
                    for tr in rows[1:]:
                        tds = tr.find_all('td')
                        if len(tds) > max(c_name, c_lots):
                            nm = tds[c_name].text.strip().replace('（株）', '').replace('株式会社', '')
                            lt = tds[c_lots].text.strip()
                            # 会社名と枚数が両方存在する場合のみ追加
                            if nm and lt and nm != "証券会社":
                                kanji_list.append(f"{nm} {lt}")
        
        # 整理した内容を「幹事団と割当」という名前で格納（空行なし）
        info['幹事団と割当'] = "\n".join(kanji_list)
                        
        return info
    except Exception as e:
        print(f"詳細情報取得エラー ({url}): {e}")
        return None

def main():
    print("IPO詳細情報を取得中（幹事団情報を精密にクリーニング）...")
    links = get_ipo_links()
    target_links = [l for l in links if re.search(r'/ipo/\d+/?$', l)]
    
    if not target_links:
        print("詳細ページへのリンクが見わたりませんでした。")
        return

    all_data = []
    for i, link in enumerate(target_links, 1):
        print(f"[{i}/{len(target_links)}] 取得中: {link}")
        details = get_detailed_info(link)
        if details:
            all_data.append(details)
        time.sleep(1)
        
    if not all_data:
        print("データが取得できませんでした。")
        return

    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True
        wb = excel.Workbooks.Add()
        sheet = wb.ActiveSheet
        sheet.Name = "IPOデータ(最終調整版)"
        
        headers_set = []
        for d in all_data:
            for k in d.keys():
                if k not in headers_set:
                    headers_set.append(k)
        
        for c_idx, head in enumerate(headers_set, 1):
            cell = sheet.Cells(1, c_idx)
            cell.Value = head
            cell.Font.Bold = True
            cell.Interior.ColorIndex = 15
        
        for r_idx, d in enumerate(all_data, 2):
            for c_idx, head in enumerate(headers_set, 1):
                val = d.get(head, "")
                cell = sheet.Cells(r_idx, c_idx)
                cell.Value = val
                if head == '幹事団と割当':
                    cell.WrapText = True
                else:
                    cell.WrapText = False
        
        sheet.Columns.AutoFit()
        sheet.Rows.AutoFit()
        sheet.Cells.VerticalAlignment = -4108
        
        print("Excelへの書き出しが正常に完了しました。")
        
    except Exception as e:
        print(f"Excel操作中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
