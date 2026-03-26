import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-less';

export function highlightCode(code: string, language: string): string {
  try {
    const grammar = Prism.languages[language] || Prism.languages.markup;
    return Prism.highlight(code, grammar, language);
  } catch {
    return code;
  }
}

export function processMarkdown(content: string): string {
  let processed = content
    // Process code blocks
    .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || 'text';
      const highlighted = highlightCode(code.trim(), language);
      return `<pre class="language-${language}" style="background: #f6f8fa; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 8px 0;"><code class="language-${language}">${highlighted}</code></pre>`;
    })
    // Process inline code
    .replace(/`([^`]+)`/g, '<code style="background: rgba(175, 184, 193, 0.2); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%;">$1</code>')
    // Process bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Process italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Process links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #99582a; text-decoration: none;">$1</a>')
    // Process paragraphs (double newlines)
    .replace(/\n\n/g, '</p><p style="margin: 8px 0;">')
    // Process line breaks
    .replace(/\n/g, '<br/>');
  
  return `<p style="margin: 8px 0;">${processed}</p>`;
}
