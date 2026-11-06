import { checkFileSize } from "./helper_functions";
import { ALLOWED_PDF_EXTENSIONS } from "../globals";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.min.mjs";

// Ensure worker is set
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/legacy/build/pdf.worker.min.mjs",
    import.meta.url,
).toString();

export default async function pdfCheck(
    file,
    max_file_size = 0,
    max_pages = 0,
    error_handler = console.error,
) {
    if (typeof file === "string") return true;

    const pdfExtension = file.name.split(".").pop().toLowerCase();
    if (
        !file.type ||
        file.type !== "application/pdf" ||
        !ALLOWED_PDF_EXTENSIONS.includes(pdfExtension)
    ) {
        error_handler(
            `Error: Selected ${file.name} file must be a pdf (${ALLOWED_PDF_EXTENSIONS.join(", ")}).`,
        );
        return false;
    }

    if (!checkFileSize(file, max_file_size, error_handler)) return false;

    if (max_pages > 0) {
        let objectUrl = null;
        try {
            // Create a temporary blob URL from the local file object
            objectUrl = URL.createObjectURL(file);

            const loadingTask = pdfjsLib.getDocument(objectUrl);
            const pdf = await loadingTask.promise;

            const totalPages = pdf.numPages;

            if (totalPages > max_pages) {
                error_handler(
                    `Error: ${file.name} has ${totalPages} pages. The maximum allowed is ${max_pages} pages.`,
                );
                return false;
            }
        } catch (error) {
            error_handler(
                `Error: Failed to read the page count of ${file.name}. The file might be corrupted.`,
            );
            return false;
        } finally {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        }
    }

    return true;
}
