// ===============================
// CampusRide Authentication
// ===============================

function getCurrentUser() {
    const user = localStorage.getItem("campusUser");

    if (!user) {
        return null;
    }

    try {
        return JSON.parse(user);
    } catch (error) {
        console.error("Invalid login data");
        localStorage.removeItem("campusUser");
        return null;
    }
}

function isLoggedIn() {
    return getCurrentUser() !== null;
}

function logout() {
    localStorage.removeItem("campusUser");
    window.location.href = "/login.html";
}

function requireLogin() {
    const user = getCurrentUser();

    if (!user) {
        window.location.href = "/login.html";
        return null;
    }

    return user;
}

function requireRole(role) {
    const user = requireLogin();

    if (!user) {
        return null;
    }

    if (user.role !== role) {
        alert("You do not have permission to access this page.");
        window.location.href = "/";
        return null;
    }

    return user;
}

function showLoggedInUser() {
    const user = getCurrentUser();

    const accountElement = document.getElementById("accountName");

    if (accountElement && user) {
        accountElement.textContent = `👋 ${user.name}`;
    }

    const loginLink = document.getElementById("loginLink");
    const logoutButton = document.getElementById("logoutButton");
    const sellerDashboardLink = document.getElementById("sellerDashboardLink") || document.getElementById("sellerLink");

    if (user) {
        if (loginLink) {
            loginLink.style.display = "none";
        }

        if (logoutButton) {
            logoutButton.style.display = "inline-block";
        }

        if (sellerDashboardLink) {
            if (user.role === "seller") {
                sellerDashboardLink.style.display = "inline-block";
            } else {
                sellerDashboardLink.style.display = "none";
            }
        }
    } else {
        if (loginLink) {
            loginLink.style.display = "inline-block";
        }

        if (logoutButton) {
            logoutButton.style.display = "none";
        }

        if (sellerDashboardLink) {
            sellerDashboardLink.style.display = "none";
        }
    }
}

document.addEventListener("DOMContentLoaded", function () {
    showLoggedInUser();
});