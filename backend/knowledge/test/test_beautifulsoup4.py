from bs4 import BeautifulSoup

# 模拟一段脏 HTML (包含脚本、内联样式、以及你不想要的广告块)
dirty_html = """
<html>
<body>
    <h1>万全T168服务器故障分析</h1>

    <script>console.log("tracking code");</script>
    <style>.red { color: red; }</style>

    <p>服务器开机有类似救护车的报警声。</p>

    <div class="content-body">
        <p>可能原因：1. 内存松动；2. 主板故障。</p>
        <img src="error.jpg" alt="报错图片">
    </div>

    <ul class="mceNonEditable">
        <li>
            <img src="ad.png">
            <span>联想专家一对一重装系统服务...广告内容...</span>
        </li>
    </ul>

    <br><br><br> </body>
</html>
"""


def clean_html_with_bs4(html_content):
    # 1. 创建 Soup 对象 (解析器推荐用 html.parser)
    soup = BeautifulSoup(html_content, 'html.parser')

    print("--- 原始结构中包含广告和脚本 ---")

    # 2. 【核心操作】切除无用元素 (Decompose)
    # decompose() 会把标签及其内容从树中彻底移除

    # A. 移除所有的 script 和 style 标签
    for tag in soup(["script", "style"]):
        tag.decompose()

    # B. 移除特定的广告类 (根据你的 JSON 数据)
    # select() 使用 CSS 选择器，非常灵活
    for ad in soup.select('.mceNonEditable'):
        ad.decompose()

    # 4. 输出清洗后的 HTML 字符串
    return str(soup)


# --- 运行测试 ---
cleaned = clean_html_with_bs4(dirty_html)

print("\n--- 清洗后的 HTML (准备交给 markdownify) ---")
print(cleaned)