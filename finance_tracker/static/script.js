// charts on the expenses page
// chartData is created in expenses/list.html from the python data

// default colors so the text is visible on dark background
Chart.defaults.color = "#cbd5e1";
Chart.defaults.borderColor = "#1e293b";

const pieCanvas = document.getElementById("pieChart");
const barCanvas = document.getElementById("barChart");

// canvas is not on the page when there are no expenses
if (pieCanvas) {
    new Chart(pieCanvas, {
        type: "pie",
        data: {
            labels: chartData.pie_labels,
            datasets: [{
                data: chartData.pie_values,
                backgroundColor: chartData.pie_colors,
                borderColor: "#ffffff",
                borderWidth: 1
            }]
        },
        options: {
            maintainAspectRatio: false
        }
    });
}

if (barCanvas) {
    new Chart(barCanvas, {
        type: "bar",
        data: {
            labels: chartData.bar_labels,
            datasets: [{
                label: "Total",
                data: chartData.bar_values,
                backgroundColor: "rgba(56, 152, 214, 0.55)",
                borderColor: "#3898d6",
                borderWidth: 1
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}
