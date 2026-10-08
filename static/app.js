let allListings = [];


// --------------------------------
// Load listings from FastAPI
// --------------------------------

async function loadListings() {

    try {

        const response = await fetch("/listings");

        allListings = await response.json();

        displayListings(allListings);

    } catch (error) {

        console.error(error);

        document.getElementById("listings").innerHTML =
            "<p>Unable to load listings.</p>";
    }
}


// --------------------------------
// Display listings
// --------------------------------

function displayListings(listings) {

    const container =
        document.getElementById("listings");


    if (listings.length === 0) {

        container.innerHTML =
            "<p>No listings found.</p>";

        return;
    }


    container.innerHTML = listings.map(item => {

        let emoji = "📦";

        if (item.category === "Cycle") {
            emoji = "🚲";
        }

        if (item.category === "Bike") {
            emoji = "🏍️";
        }

        if (item.category === "Scooty") {
            emoji = "🛵";
        }


        return `

            <div class="card">

                <div class="card-image">

                    ${emoji}

                </div>


                <div class="card-content">

                    <div class="card-category">

                        ${item.category}

                    </div>


                    <h3>
                        ${item.title}
                    </h3>


                    <div class="price">

                        ₹${Number(item.price).toLocaleString("en-IN")}

                    </div>


                    <div class="condition">

                        Condition:
                        ${item.condition}

                    </div>


                    <button
                        class="view-btn"
                        onclick="viewListing(${item.id})"
                    >

                        View Details

                    </button>

                </div>

            </div>

        `;

    }).join("");
}


// --------------------------------
// View listing
// --------------------------------

function viewListing(id) {

    window.location.href =
        `/static/listing.html?id=${id}`;

}


// --------------------------------
// Search
// --------------------------------

document
    .getElementById("searchInput")
    .addEventListener("input", function () {

        const search =
            this.value.toLowerCase();


        const filtered =
            allListings.filter(item =>

                item.title
                    .toLowerCase()
                    .includes(search)

                ||

                item.category
                    .toLowerCase()
                    .includes(search)

            );


        displayListings(filtered);

    });


// --------------------------------
// Categories
// --------------------------------

document
    .querySelectorAll(".category")
    .forEach(button => {

        button.addEventListener("click", function () {

            document
                .querySelectorAll(".category")
                .forEach(btn =>
                    btn.classList.remove("active")
                );


            this.classList.add("active");


            const category =
                this.dataset.category;


            if (category === "All") {

                displayListings(allListings);

                return;
            }


            const filtered =
                allListings.filter(item =>
                    item.category === category
                );


            displayListings(filtered);

        });

    });


// --------------------------------
// Start
// --------------------------------

loadListings();