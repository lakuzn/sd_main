export function linkify(text) {
    if (!text) return '';

    const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;

    return text.replace(urlRegex, (url) => {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">
                    ${url}
                </a>`;
    });
}