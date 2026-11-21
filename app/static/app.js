
const $ = (id) => document.getElementById(id);

let customers = [];

function money(amount) {
    return "৳" + Number(amount).toLocaleString("en-BD", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// API communication
async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
    }

    return data;
}


// LOAD DASHBOARD
async function loadDashboard() {
    const data = await api("/api/dashboard");

    $("totalDue").textContent = money(data.total_due);
    $("totalCustomers").textContent = data.total_customers;
    $("totalReceived").textContent = money(data.total_received);
}


// LOAD CUSTOMERS
async function loadCustomers(search = "") {
    customers = await api(
        "/api/customers?search=" + encodeURIComponent(search)
    );

    const table = $("customerTable");
    table.replaceChildren();

    customers.forEach(customer => {
        const row = document.createElement("tr");

        const name = document.createElement("td");
        name.textContent = customer.name;

        const phone = document.createElement("td");
        phone.textContent = customer.phone || "-";

        const balance = document.createElement("td");
        balance.textContent = money(customer.balance);
        balance.className = customer.balance > 0 ? "due" : "payment";

        const action = document.createElement("td");
        const button = document.createElement("button");

        button.textContent = "History";
        button.className = "view-btn";

        button.addEventListener("click", () => {
            $("historyCustomer").value = customer.id;
            loadHistory();
            $("historyTable").scrollIntoView({ behavior: "smooth" });
        });

        action.appendChild(button);

        row.append(name, phone, balance, action);
        table.appendChild(row);
    });

    // Update customer dropdowns
    const selects = [
        $("transactionCustomer"),
        $("historyCustomer")
    ];

    selects.forEach(select => {
        const previousValue = select.value;

        select.replaceChildren();

        const defaultOption = document.createElement("option");
        defaultOption.value = "";

        defaultOption.textContent =
            select.id === "transactionCustomer"
                ? "Select customer"
                : "All Customers";

        select.appendChild(defaultOption);

        customers.forEach(customer => {
            const option = document.createElement("option");
            option.value = customer.id;
            option.textContent = customer.name;
            select.appendChild(option);
        });

        select.value = previousValue;
    });
}


// ADD CUSTOMER
$("customerForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
        await api("/api/customers", {
            method: "POST",
            body: JSON.stringify({
                name: $("customerName").value,
                phone: $("customerPhone").value,
                address: $("customerAddress").value
            })
        });

        $("customerForm").reset();

        await loadEverything();

        alert("Customer added successfully!");

    } catch (error) {
        alert(error.message);
    }
});


// SEARCH CUSTOMER
let searchTimeout;

$("searchCustomer").addEventListener("input", () => {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        loadCustomers($("searchCustomer").value);
    }, 250);
});


// ADD DUE OR RECEIVE PAYMENT
$("transactionForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = $("transactionMessage");

    message.textContent = "";
    message.style.color = "";

    try {
        const result = await api("/api/transactions", {
            method: "POST",
            body: JSON.stringify({
                customer_id: $("transactionCustomer").value,
                type: $("transactionType").value,
                amount: $("transactionAmount").value,
                note: $("transactionNote").value
            })
        });

        message.textContent =
            result.message + ". Remaining due: " + money(result.balance);

        $("transactionForm").reset();

        await loadEverything();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "#dc3545";
    }
});


// TRANSACTION HISTORY
async function loadHistory() {
    const customerId = $("historyCustomer").value;
    const type = $("historyType").value;

    const params = new URLSearchParams();

    if (customerId) params.set("customer_id", customerId);
    if (type) params.set("transaction_type", type);

    const data = await api("/api/transactions?" + params.toString());

    const table = $("historyTable");
    table.replaceChildren();

    data.forEach(item => {
        const row = document.createElement("tr");

        const date = document.createElement("td");
        date.textContent = item.created_at
            ? new Date(item.created_at).toLocaleString()
            : "-";

        const name = document.createElement("td");
        name.textContent = item.customer_name;

        const transactionType = document.createElement("td");
        transactionType.textContent =
            item.type === "due" ? "বাকি" : "জমা";

        transactionType.className = item.type;

        const amount = document.createElement("td");
        amount.textContent = money(item.amount);
        amount.className = item.type;

        const note = document.createElement("td");
        note.textContent = item.note || "-";

        row.append(date, name, transactionType, amount, note);
        table.appendChild(row);
    });
}


// HISTORY FILTERS
$("historyCustomer").addEventListener("change", loadHistory);
$("historyType").addEventListener("change", loadHistory);


// LOAD EVERYTHING
async function loadEverything() {
    await loadDashboard();
    await loadCustomers();
    await loadHistory();
}


// START APPLICATION
async function startApplication() {
    try {
        await loadEverything();
    } catch (error) {
        alert("Application loading error: " + error.message);
        console.error(error);
    }
}

startApplication();
