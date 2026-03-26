export function formatScore(score: number): string {
  return score.toFixed(3);
}

export function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  
  return date.toLocaleDateString('zh-CN');
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function escapeHtml(str: string): string {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export function highlightText(text: string, keywords: string[]): string {
  if (!keywords.length) return escapeHtml(text);
  
  const escapedText = escapeHtml(text);
  const escapedKeywords = keywords.map(k => 
    k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  );
  
  const regex = new RegExp(
    `(${escapedKeywords.join('|')})`,
    'gi'
  );
  
  return escapedText.replace(regex, '<mark style="background-color: rgba(201, 125, 96, 0.3); padding: 0 2px; border-radius: 2px;">$1</mark>');
}
