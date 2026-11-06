import React from "react";
import { useAuth } from "../context/AuthContext";

// function to return true for allowed things, and false for not having permission
export default function HasPermission(permission_type, id_check = -1) {
    // permission_type: ["admin", "logged_in", "guest"]
    const { authInfo } = useAuth();

    if (authInfo.is_authenticated && authInfo.is_admin) {
        return true;
    } // admin can do everything

    if (id_check == -1) {
        // if there is no id we need to match to do permission check
        if (authInfo.is_authenticated && permission_type !== "admin") {
            return true;
        } // logged in user can do everything except the admin stuff
        else if (!authInfo.is_authenticated && permission_type == "guest") {
            return true;
        } // non logged in user can do only guest stuff
    } else if (Array.isArray(id_check)) {
        // id_check is a list for manga collaborator permissions
        if (
            permission_type === "logged_in" &&
            id_check.includes(authInfo.profile_id)
        ) {
            return true;
        }
    } else {
        // if we have an id to check (for example edit profile page is only visible to the correct logged_in user)
        if (
            authInfo.is_authenticated &&
            permission_type === "logged_in" &&
            authInfo.profile_id == id_check
        ) {
            return true;
        } // logged_in user can do this if it has the correct profile_id
    }
    return false;
}
