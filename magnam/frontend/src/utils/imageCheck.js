import { checkFileSize } from "./helper_functions";
import { ALLOWED_IMAGE_EXTENSIONS } from "../globals";

export default async function imageCheck(
    file,
    min_height = 0,
    max_height = 0,
    min_width = 0,
    max_width = 0,
    max_file_size = 0,
    error_handler = console.error,
) {
    const DEFAULT_MAX_DIMENSION = 8096;
    const DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
    max_width = max_width || DEFAULT_MAX_DIMENSION;
    max_height = max_height || DEFAULT_MAX_DIMENSION;
    max_file_size = max_file_size || DEFAULT_MAX_FILE_SIZE;

    if (typeof file === "string") return true;

    const imageExtension = file.name.split(".").pop().toLowerCase();
    if (
        !file.type ||
        !file.type.startsWith("image/") ||
        !ALLOWED_IMAGE_EXTENSIONS.includes(imageExtension)
    ) {
        error_handler(
            `Error: Selected ${file.name} file must be an image (${ALLOWED_IMAGE_EXTENSIONS.join(", ")}).`,
        );
        return false;
    }

    if (!checkFileSize(file, max_file_size, error_handler)) return false;

    // check dimensions using a blob URL; revoke it afterwards
    let objectUrl = null;
    try {
        objectUrl = URL.createObjectURL(file);
        const img = await new Promise((resolve, reject) => {
            const imageObj = new Image();
            imageObj.onload = () => resolve(imageObj);
            imageObj.onerror = () => reject(new Error("Invalid image file"));
            imageObj.src = objectUrl;
        });

        if (
            (min_width && img.width < min_width) ||
            (min_height && img.height < min_height)
        ) {
            error_handler(
                `Error: ${file.name} file width must be at least ${min_width}px height must be at least ${min_height}px`,
            );
            return false;
        }

        if (
            (max_width && img.width > max_width) ||
            (max_height && img.height > max_height)
        ) {
            error_handler(
                `Error: ${file.name} file width must be at most ${max_width}px height must be at most ${max_height}px`,
            );
            return false;
        }

        return true;
    } catch (err) {
        error_handler(
            `Error: Could not read ${file.name} file for width/height dimension check`,
        );
        return false;
    } finally {
        if (objectUrl) URL.revokeObjectURL(objectUrl);
    }
}
