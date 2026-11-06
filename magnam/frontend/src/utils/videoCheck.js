import { checkFileSize } from "./helper_functions";
import { ALLOWED_VIDEO_EXTENSIONS } from "../globals";

export default async function videoCheck(
    file,
    min_height = 0,
    max_height = 0,
    min_width = 0,
    max_width = 0,
    min_duration = 0,
    max_duration = 0,
    max_file_size = 0,
    error_handler = console.error,
) {
    if (typeof file === "string") return true;

    const videoExtension = file.name.split(".").pop().toLowerCase();
    if (
        !file.type ||
        !file.type.startsWith("video/") ||
        !ALLOWED_VIDEO_EXTENSIONS.includes(videoExtension)
    ) {
        error_handler(
            `Error: ${file.name} must be a valid video (${ALLOWED_VIDEO_EXTENSIONS.join(", ")}).`,
        );
        return false;
    }

    if (!checkFileSize(file, max_file_size, error_handler)) return false;

    let objectUrl = null;
    try {
        objectUrl = URL.createObjectURL(file);

        const video = document.createElement("video");
        video.preload = "metadata";

        const loaded = await new Promise((resolve, reject) => {
            video.onloadedmetadata = () => resolve(video);
            video.onerror = () => reject("Invalid video file");
            video.src = objectUrl;
        });

        if (
            (min_duration && loaded.duration < min_duration) ||
            (max_duration && loaded.duration > max_duration)
        ) {
            error_handler(
                `${file.name} file (${loaded.duration} seconds) must be at least ${min_duration} and at most ${max_duration} seconds`,
            );
            return false;
        }

        // Width & height validation
        if (
            (min_width && loaded.videoWidth < min_width) ||
            (min_height && loaded.videoHeight < min_height)
        ) {
            error_handler(
                `${file.name} file width must be at least ${min_width}px height must be at least ${min_height}px`,
            );
            return false;
        }

        if (
            (max_width && loaded.videoWidth > max_width) ||
            (max_height && loaded.videoHeight > max_height)
        ) {
            error_handler(
                `${file.name} file width must be at most ${max_width}px height must be at most ${max_height}px`,
            );
            return false;
        }

        return true;
    } catch (e) {
        error_handler(`Error validating ${file.name} file.`);
        return false;
    } finally {
        if (objectUrl) URL.revokeObjectURL(objectUrl);
    }
}
