from pypdf import PdfReader

# PDF文件路径
pdf_path = "Liu 等 - 2023 - Mapping tree species diversity in temperate montane forests using sentinel-1 and sentinel-2 imagery .pdf"
# 输出文本文件路径
txt_path = "research_paper.txt"

try:
    # 打开PDF文件
    reader = PdfReader(pdf_path)
    
    # 获取PDF页数
    num_pages = len(reader.pages)
    print(f"PDF总页数: {num_pages}")
    
    # 提取所有页面文本
    full_text = ""
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text = page.extract_text()
        if text:
            full_text += f"--- 第 {page_num + 1} 页 ---\n"
            full_text += text
            full_text += "\n\n"
    
    # 保存为文本文件
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(f"PDF已成功转换为文本，保存为: {txt_path}")
    print(f"转换的文本长度: {len(full_text)} 字符")
    
except Exception as e:
    print(f"转换过程中出现错误: {str(e)}")
