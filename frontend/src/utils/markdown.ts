import MarkdownIt from 'markdown-it'
import mkKatex from 'markdown-it-katex'
import 'katex/dist/katex.min.css'

const md = MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
}).use(mkKatex)

export function renderMarkdown(text: string) {
  // 自动将 $$...$$ 块级公式前后加换行，避免和文字混排
  const fixed = text.replace(/\$\$(.+?)\$\$/gs, '\n$$$1$$\n')
  return md.render(fixed)
}
