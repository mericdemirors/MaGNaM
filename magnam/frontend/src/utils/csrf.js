export function getCookie(name) {
    if (typeof document === "undefined") return null;

    const cookieStr = document.cookie || "";
    const parts = cookieStr.split("; ").map((c) => c.split("="));

    for (let [k, v] of parts) {
        if (k === name) return decodeURIComponent(v || "");
    }
    return null;
}

export async function apiFetch(url, options = {}) {
    const defaultOptions = {
        credentials: "include", // make sure cookies (sessionid, csrftoken) are sent
        headers: {},
    };

    const opts = { ...defaultOptions, ...options };
    opts.headers = {
        ...(defaultOptions.headers || {}),
        ...(options.headers || {}),
    };

    const method = (opts.method || "GET").toUpperCase();

    if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
        const csrftoken = getCookie("csrftoken");
        if (csrftoken) {
            opts.headers["X-CSRFToken"] = csrftoken;
        }
        if (
            opts.body &&
            !(opts.body instanceof FormData) &&
            !opts.headers["Content-Type"]
        ) {
            opts.headers["Content-Type"] = "application/json";
        }
    }
    const response = await fetch(url, opts);
    return response;
}

export async function handleFetch(process_name, response) {
    /*
        1- if error_message exists -> something went wrong
        2- if error_message doesn't exists:
            2.1 -> if success_data exists -> it went well
            2.2 -> something deleted successfull with no body to return
    */
    let success_data = null;
    let error_message = null;

    try {
        // Try to parse JSON, but handle cases like 204 No Content
        const text = await response.text();
        const data = text ? JSON.parse(text) : null;
        if (response.ok) {
            // Handle successful responses
            if (!data) {
                success_data = null;
            } // e.g., HTTP 204 No Content
            else if (data.data) {
                success_data = data.data;
            } // Standard success with data field
            else {
                success_data = data;
            } // Unexpected but valid payload
        } else {
            // Handle non-OK (error) responses
            if (data?.error?.error_message) {
                error_message = `${process_name}: ${data.error.error_message}`;
            } else if (data?.error_message) {
                error_message = `${process_name}: ${data.error_message}`;
            } // Sometimes direct error_message
            else if (data && typeof data === "object") {
                error_message = `${process_name}: ${JSON.stringify(data)}`;
            } // Could be serializer or validation dict
            else {
                error_message = `${process_name}: Unknown error (status ${response.status})`;
            }
        }
    } catch (err) {
        // JSON parse or network-related error
        error_message = `JSON parsing error while ${process_name}: ${[err.message]}`;
    }
    error_message = formatDetailedError(error_message);

    return [success_data, error_message, response.ok];
}

function formatDetailedError(rawMessage) {
    if (!rawMessage || typeof rawMessage !== "string") return rawMessage;

    try {
        const firstColonIndex = rawMessage.indexOf(": ");
        if (firstColonIndex === -1) return rawMessage;

        const jsonString = rawMessage.substring(firstColonIndex + 2);
        let errorObj = JSON.parse(jsonString);

        // If it's not an object, just return the raw text part
        if (typeof errorObj !== "object" || errorObj === null) {
            return jsonString;
        }

        // UNPACK STEP: If the JSON is wrapped in an { error: {...} } wrapper, drill down into it
        if (
            errorObj.error &&
            typeof errorObj.error === "object" &&
            !Array.isArray(errorObj.error)
        ) {
            errorObj = errorObj.error;
        }

        // Helper function to format values dynamically (strings, arrays, or sub-objects)
        const formatValue = (val, indent = "  ") => {
            if (Array.isArray(val)) {
                return val.map((msg) => `${indent}-${msg}`).join("\n");
            } else if (typeof val === "object" && val !== null) {
                // Handle deeper nested objects if they occur
                return Object.entries(val)
                    .map(
                        ([subKey, subVal]) =>
                            `${indent}${subKey}:\n${formatValue(subVal, indent + "  ")}`,
                    )
                    .join("\n");
            }
            // Plain string or number
            return `${indent}-${val}`;
        };

        return Object.entries(errorObj)
            .map(([key, value]) => {
                return `${key}:\n${formatValue(value)}`;
            })
            .join("\n");
    } catch (e) {
        // If parsing fails, it's a plain text error, just strip the process prefix
        return rawMessage.replace(/^.*?: /, "");
    }
}
