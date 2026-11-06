import { checkFileSize } from "./helper_functions";
import { ALLOWED_AUDIO_EXTENSIONS } from "../globals";

export default async function audioCheck(
    file,
    min_duration = 0,
    max_duration = 0,
    max_file_size = 0,
    error_handler = console.error,
) {
    if (typeof file === "string") return true;

    const audioExtension = file.name.split(".").pop().toLowerCase();
    if (
        !file.type ||
        !file.type.startsWith("audio/") ||
        !ALLOWED_AUDIO_EXTENSIONS.includes(audioExtension)
    ) {
        error_handler(
            `Error: ${file.name} must be a valid audio file (${ALLOWED_AUDIO_EXTENSIONS.join(", ")}).`,
        );
        return false;
    }

    if (!checkFileSize(file, max_file_size, error_handler)) return false;

    let objectUrl = null;
    try {
        objectUrl = URL.createObjectURL(file);

        const audio = document.createElement("audio");

        const loaded = await new Promise((resolve, reject) => {
            audio.onloadedmetadata = () => resolve(audio);
            audio.onerror = () => reject("Invalid audio file");
            audio.src = objectUrl;
        });

        if (
            (min_duration && loaded.duration < min_duration) ||
            (max_duration && loaded.duration > max_duration)
        ) {
            error_handler(
                `${file.name} file (${loaded.duration} seconds) must be at least ${min_duration} seconds and at most ${max_duration} seconds long`,
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
