const currentUser = requireRole("seller");

if (!currentUser) {
    throw new Error("Seller authentication required.");
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function loadSellerDashboard() {

    try {

        const response =
            await fetch(
                `/my-listings?student_id=${encodeURIComponent(currentUser.student_id)}`
            );

        if (!response.ok) {
            throw new Error("Could not load your listings");
        }

        const listings =
            await response.json();


        displayListings(listings);

        loadOffers(listings);


    } catch (error) {

        console.error(error);
        const container = document.getElementById("myListings");
        if (container) {
            container.innerHTML = "<p>Error loading listings. Please refresh.</p>";
        }

    }

}


// ============================
// DISPLAY LISTINGS
// ============================

function displayListings(listings) {

    const container =
        document.getElementById("myListings");


    if (listings.length === 0) {

        container.innerHTML =
            "<p>You haven't posted any listings yet. Click <strong>+ Sell Something</strong> to add one!</p>";

        return;
    }


    container.innerHTML =
        listings.map(item => {

            return `

                <div class="dashboard-card">

                    <div>

                        <h3>
                            ${escapeHtml(item.title)}
                        </h3>

                        <p>
                            ${escapeHtml(item.category)}
                        </p>

                        <strong>
                            ₹${Number(item.price)
                                .toLocaleString("en-IN")}
                        </strong>

                        <p>
                            Condition:
                            ${escapeHtml(item.condition)}
                        </p>

                    </div>


                    <a
                        href="/listing.html?id=${Number(item.id)}"
                        class="view-btn"
                        style="text-decoration: none;"
                    >
                        View Listing
                    </a>

                </div>

            `;

        }).join("");

}


// ============================
// LOAD BUYER OFFERS
// ============================

async function loadOffers(listings) {

    const container =
        document.getElementById("offers");

    let allOffers = [];


    for (const listing of listings) {

        try {
            const response =
                await fetch(
                    `/messages/${listing.id}`
                );

            if (!response.ok) continue;

            const messages =
                await response.json();


            messages.forEach(message => {

                if (message.offer_price) {

                    allOffers.push({

                        listing: listing,

                        offer: message

                    });

                }

            });
        } catch (err) {
            console.error("Error loading offers for listing:", listing.id, err);
        }

    }


    if (allOffers.length === 0) {

        container.innerHTML = `
            <p>
                No buyer offers yet.
            </p>
        `;

        return;
    }


    container.innerHTML =
        allOffers.map(item => {

            return `

                <div class="offer-card">

                    <h3>
                        ${escapeHtml(item.listing.title)}
                    </h3>

                    <p>
                        Buyer:
                        <strong>${escapeHtml(item.offer.sender)}</strong>
                    </p>

                    <div class="buyer-offer">

                        💰 ₹${Number(
                            item.offer.offer_price
                        ).toLocaleString("en-IN")}

                    </div>

                    <p>
                        ${escapeHtml(item.offer.message)}
                    </p>

                    <a
                        href="/listing.html?id=${Number(item.listing.id)}"
                        class="view-btn"
                        style="display: inline-block; margin-top: 10px; text-decoration: none; width: auto; padding: 10px 18px;"
                    >
                        Reply / Open Chat
                    </a>

                </div>

            `;

        }).join("");

}


loadSellerDashboard();