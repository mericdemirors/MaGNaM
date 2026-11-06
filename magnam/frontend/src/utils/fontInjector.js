export const injectFontFromBlob = (fontName, blob) => {
    const url = URL.createObjectURL(blob);

    const style = document.createElement("style");

    style.setAttribute("data-font", fontName);

    style.innerHTML = `
        @font-face {
            font-family: '${fontName}';
            src: url('${url}');
        }
    `;

    document.head.appendChild(style);
};
