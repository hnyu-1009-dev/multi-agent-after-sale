from markdownify import markdownify as md
import  re
# 1. HTML 内容
# 这是从知识库网页上爬取下来的内容片段

# origin_html_content="""
# <html>\n <head></head>\n <body>\n  <p>万全T168<a href=\"/detail/kd_17589.html\" target=\"_blank\">服务器</a>在开机无显时会提示一种类似救护车的报警声，已经有录音，见附件：</p>\n  <p><br></p>\n  <p>此问题现在有两种情况：<br><br>1、<a href=\"/detail/kd_17351.html\" target=\"_blank\">内存</a>接触问题：重新插拔后可以解决；此问题已经复现，拔下内存后会提示类似救护车声音；</p>\n  <p><br></p>\n  <p>2、<a href=\"/detail/kd_17352.html\" target=\"_blank\">主板</a>故障：在第１步无法解决情况下，多起报修案例表明与主板故障有关；维修站上门更换主板解决；</p>\n  <p><br></p>\n  <p>3、可能故障件：主板和内存。</p>\n  <p><br></p>\n  <p>报警声录音文件见附件：<a href=\"https://webdoc.lenovo.com.cn/lenovowsi/cskb/data/2005-04-29/15665/T168 救护车报警声.mp3\" target=\"_self\">T168 救护车报警声.mp3</a></p>\n  <p><br></p>\n  <p>附加文档2:<a href=\"https://webdoc.lenovo.com.cn/lenovowsi/cskb/data/2005-06-06/15665/TL460用户手册.pdf\"><img src=\"http://support.lenovo.com.cn/lenovo/wsi/support/ico/pdf.gif\" border=\"0\"> TL460用户手册.pdf</a></p>\n  <p></p>\n  <p></p>\n </body>\n</html>
# """
origin_html_content="""
<html>\n <head></head>\n <body>\n  <p><strong>解决方案</strong><strong>：</strong></p>\n  <p>&nbsp;</p>\n  <p>利用软碟通软件（UltraISO）实现</p>\n  <p>&nbsp;</p>\n  <p>一、双击软碟通软件UltraISO，选择“文件”---“打开”找到Windows 7操作系统的光盘镜像ISO文件，单</p>\n  <p>击“启动光盘”---“写入硬盘映像”；</p>\n  <p>&nbsp;</p>\n  <p><img src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160128/1453944749628319.jpg\" alt=\"\"></p>\n  <p><br>二、点击“写入”将镜像文件写入U盘，注意在“硬盘驱动器”列表谨慎选择磁盘，如下图所示：</p>\n  <p>&nbsp;</p>\n  <p><img title=\"1622802922519206.png\" src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20210604/1622802922519206.png\" alt=\"w0002如何使用U盘安装Windows 7操作系统第2张图.png\"></p>\n  <p>&nbsp;</p>\n  <p>&nbsp;</p>\n  <p>&nbsp;</p>\n  <p><strong>注意事项：</strong>此操作会格式化所选择的U盘，操作一定谨慎！</p>\n  <p>&nbsp;</p>\n  <p>此方法同时适用Windows Vista、Windows Server2008及Windows Server2008R2各版本。</p>\n  <ul style=\"padding: 10px 0px; width: 94%;\">\n   <li class=\"mceNonEditable require_0x2ae48d04\" style=\"list-style: none; max-height: 400px; overflow-y: auto;\" contenteditable=\"false\"><p><img src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20190523/1558590983697581.png\" width=\"30\" height=\"21\"><span style=\"font-size: 16px;\">安装或升级系统太麻烦？没有时间？<a href=\"https://item.lenovo.com.cn/product/1000630.html?pmf_group=23as&amp;pmf_medium=23as&amp;pmf_source=Z00005044T000\"><span style=\"text-decoration: underline; color: blue;\">联想专家一对一重装系统服务</span></a>，通过远程的方式重装系统，让电脑重新恢复活力，速度更快；清除电脑存在的潜在威胁，让您的数据更安全！</span></p></li>\n  </ul>\n </body>\n</html>
"""

print(origin_html_content)


# structured_html_content = """
# <html>
#  <head></head>
#  <body>
#   <p>&nbsp;</p>
#   <p><strong>故障现象:</strong></p>
#   <p><br>如何去掉 Outlook 中的段落标记等符号。</p>
#   <p><br><strong>解决方案:</strong></p>
#   <p><br><strong>如何去掉 Outlook 中的段落标记等符号</strong><br><br><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690803.png"><br>&nbsp;</p>
#   <p><br>只要在编辑器中将它们隐藏就行了。具体如下：</p>
#   <p><br></p>
#   <h4 id="tocHeadRef">对于 Outlook 2010</h4>
#   <p><br></p>
#   <p>新建一份电子邮件，打开“<strong class="uiterm">文件</strong>”选项卡，单击“<strong class="uiterm">选项</strong>”。<br></p>
#   <p>&nbsp;</p>
#   <p><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690804.png"></p>
#   <p><br>在选项窗口左侧单击“<strong class="uiterm">邮件</strong>”，按一下“<strong class="uiterm">编辑器选项</strong>”按钮。<br></p>
#   <p>&nbsp;</p>
#   <p><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690805.png"></p>
#   <p><br>“<strong class="uiterm">显示</strong>”窗格右侧有一个“<strong class="uiterm">始终在屏幕上显示这些格式标记</strong>”列表，取消对“<strong class="uiterm">段落标记</strong>”的勾选。<br></p>
#   <p>&nbsp;</p>
#   <p><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690806.png"><br></p>
#   <h4 id="tocHeadRef">对于 Outlook 2007</h4>
#   <p>建立一封新的电子邮件，按一下 Office 按钮，单击“<strong class="uiterm">编辑器选项</strong>”。<br></p>
#   <p>&nbsp;</p>
#   <p><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690807.png"></p>
#   <p><br>从左侧窗格中单击“<strong class="uiterm">显示</strong>”，然后取消对“<strong class="uiterm">段落标记</strong>”的勾选。<br></p>
#   <p>&nbsp;</p>
#   <p><img title="" class="graphic" alt="" src="http://support.microsoft.com/Library/Images/2690808.png"></p>
#   <p><br><strong class="uiterm">PS：</strong><span style="text-decoration: underline;">对于邮件中的其它编辑符号，都可以通过取消相应勾选将其消除</span></p>
#  </body>
# </html>
# """

# # 2. 调用 md()
markdown_content = md(origin_html_content)

#
# # # 3. 打印结果对比
# print("-" * 20 + " 原始 HTML " + "-" * 20)
# print(structured_html_content)
#
# print("\n" + "-" * 20 + " 转换后的 Markdown " + "-" * 20)
print(markdown_content)

# 4. 验证结果(可以把打印出来的内容复制到 Markdown 编辑器里看看效果）