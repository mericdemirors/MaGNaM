export function validateText({
    value,
    fieldName,
    minLen,
    maxLen,
    error_handler,
    required = false,
}) {
    const trimmed = value?.trim?.() ?? "";
    if (required && trimmed.length === 0) {
        error_handler(`${fieldName} is required`);
        return false;
    }

    if (trimmed.length < minLen) {
        error_handler(`${fieldName} must be at least ${minLen} characters`);
        return false;
    }
    if (maxLen !== undefined && trimmed.length > maxLen) {
        error_handler(`${fieldName} can be at most ${maxLen} characters`);
        return false;
    }

    return true;
}

export function validateLinks({
    value,
    fieldName = "links",
    minLen,
    maxLen,
    error_handler,
    required = false,
}) {
    if (typeof value !== "string") {
        error_handler(`${fieldName} must be a string`);
        return false;
    }

    const trimmed = value?.trim?.() ?? "";
    if (required && trimmed.length === 0) {
        error_handler(`${fieldName} is required`);
        return false;
    }

    const rawLinks = value.split(/\s+/).filter(Boolean);
    const cleanedLinks = [];
    for (const link of rawLinks) {
        const trimmed = link.trim();

        if (!trimmed.startsWith("https:")) {
            error_handler(`All ${fieldName} must start with https:`);
            return false;
        }

        cleanedLinks.push(trimmed);
    }

    const totalLen = cleanedLinks.join("").length;
    if (totalLen < minLen) {
        error_handler(`${fieldName} must be at least ${minLen} characters`);
        return false;
    }
    if (maxLen !== undefined && totalLen > maxLen) {
        error_handler(`${fieldName} can be at most ${maxLen} characters`);
        return false;
    }

    return true;
}

export function validateNumber({
    value,
    fieldName,
    minVal,
    maxVal,
    error_handler,
    required = false,
}) {
    // Handle empty or missing values first if field is optional
    if (value === undefined || value === null || String(value).trim() === "") {
        if (required) {
            error_handler(`${fieldName} is required`);
            return false;
        }
        return true;
    }

    const parsedNum = parseInt(value, 10);
    if (isNaN(parsedNum) || !Number.isInteger(Number(value))) {
        error_handler(`${fieldName} must be a number`);
        return false;
    }

    if (minVal !== undefined && parsedNum < minVal) {
        error_handler(`${fieldName} must be at least ${minVal}`);
        return false;
    }
    if (maxVal !== undefined && parsedNum > maxVal) {
        error_handler(`${fieldName} can be at most ${maxVal}`);
        return false;
    }

    return true;
}

export function validatePKRelation({
    value,
    fieldName = "tags",
    minCount,
    maxCount,
    error_handler,
    required = false,
}) {
    if (!Array.isArray(value)) {
        error_handler(`${fieldName} must be a list/collection`);
        return false;
    }

    if (required && value.length === 0) {
        error_handler(`${fieldName} is required`);
        return false;
    }

    if (minCount !== undefined && value.length < minCount) {
        error_handler(`At least ${minCount} ${fieldName} must be selected`);
        return false;
    }
    if (maxCount !== undefined && value.length > maxCount) {
        error_handler(`You can select at most ${maxCount} ${fieldName}`);
        return false;
    }

    return true;
}
