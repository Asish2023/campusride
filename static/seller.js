const currentUser = requireRole("seller");

if (!currentUser) {
    throw new Error("Seller authentication required.");
}

async function loadSellerDashboard() {

    try {

        const response =
            await fetch(
                `/my-listings?student_id=${encodeURIComponent(currentUser.student_id)}`
            );

        const listings =
            await response.json();


        displayListings(listings);

        loadOffers(listings);


    } catch (error) {

        console.error(error);

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
            "<p>No listings yet.</p>";

        return;
    }


    container.innerHTML =
        listings.map(item => {

            return `

                <div class="dashboard-card">

                    <div>

                        <h3>
                            ${item.title}
                        </h3>

                        <p>
                            ${item.category}
                        </p>

                        <strong>
                            ₹${Number(item.price)
                                .toLocaleString("en-IN")}
                        </strong>

                        <p>
                            Condition:
                            ${item.condition}
                        </p>

                    </div>


                    <a
                        href="/listing.html?id=${item.id}"
                        class="view-btn"
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

        const response =
            await fetch(
                `/messages/${listing.id}`
            );

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
                        ${item.listing.title}
                    </h3>

                    <p>
                        Buyer:
                        ${item.offer.sender}
                    </p>

                    <div class="buyer-offer">

                        💰 ₹${Number(
                            item.offer.offer_price
                        ).toLocaleString("en-IN")}

                    </div>

                    <p>
                        ${item.offer.message}
                    </p>

                    <button
                        onclick="alert('Counter-offer feature next!')"
                    >
                        Counter Offer
                    </button>

                </div>

            `;

        }).join("");

}


loadSellerDashboard();