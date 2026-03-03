fetch("/download/processed_lstm.csv")
    .then((response) => response.text())
    .then((csvData) => {
        const parsedData = parseCSV(csvData);
        initializeChart(parsedData);
    })
    .catch((error) => console.error("Error loading CSV:", error));

score_issuer={}

function parseCSV(csv) {
    const rows = csv.split("\n");
    const stockData = {};

    rows.forEach((row, index) => {
        if (index === 0 || row.trim() === "") return; // Skip the header row and empty lines
        const fields = row.split(",");

        const rawDate = fields[0];
        const [day, month, year] = rawDate.split("."); // Parse DD.MM.YYYY format
        const formattedDate = `${year}-${month}-${day}`; // Convert to YYYY-MM-DD
        const close = parseFloat(fields[1]);
        const closePred = parseFloat(fields[2]);
        const stockCode = fields[3];
        const score = parseFloat(fields[4]);

        if (!stockData[stockCode]) {
            stockData[stockCode] = [];
        }

        if(!score_issuer[stockCode]){
            score_issuer[stockCode]=score
        }

        if (!isNaN(close) && !isNaN(closePred) && !isNaN(score)) {
            stockData[stockCode].push([formattedDate, close, closePred, score]);
        }
    });

    return stockData;
}

function formatCloseData(stockData) {
    return stockData.map((item) => [
        new Date(item[0]).getTime(), // Convert formattedDate to timestamp
        item[1], // close price
    ]);
}

function formatPredictedData(stockData) {
    return stockData.map((item) => [
        new Date(item[0]).getTime(), // Convert formattedDate to timestamp
        item[2], // predicted close price
    ]);
}


function initializeChart(stockData) {
    const stockSelector = document.getElementById("stockSelector");
    Object.keys(stockData).forEach((stockCode) => {
        const option = document.createElement("option");
        option.value = stockCode;
        option.textContent = stockCode;
        stockSelector.appendChild(option);
    });

    const stockCode = Object.keys(stockData)[0];

    const chart = Highcharts.stockChart("container", {
        chart: { height: 600 },
        title: { text: stockCode },
        yAxis: [
            { height: "60%" },
            { top: "60%", height: "20%" },
        ],

        tooltip: {
            pointFormatter: function () {
                return (
                    "<b>" +
                    this.series.name + // Use the series name to distinguish between actual and predicted
                    "</b><br>" +
                    "Value: " +
                    Highcharts.numberFormat(this.y, 2, ",", ".") +
                    "<br>" +
                    "Date: " +
                    Highcharts.dateFormat("%e %b %Y", this.x)
                );
            },
        },

        series: [
            {
                type: "line",
                id: "close",
                name: stockCode + " Close Price",
                data: formatCloseData(stockData[stockCode]),
            },
            {
                type: "line",
                id: "closePred",
                name: stockCode + " Predicted Close Price",
                data: formatPredictedData(stockData[stockCode]),
            },
        ],
    });

    stockSelector.addEventListener("change", function () {
        const selectedStock = stockSelector.value;
        chart.series[0].setData(formatCloseData(stockData[selectedStock]));
        chart.series[1].setData(formatPredictedData(stockData[selectedStock]));
        chart.setTitle({ text: selectedStock }); // Update the title
        chart.series[0].update({ name: selectedStock + " Close Price" });
        chart.series[1].update({ name: selectedStock + " Predicted Close Price" });

        document.getElementById("score_container").innerHTML="Score for : <b>"+ selectedStock +
            "</b> is "+ score_issuer[selectedStock]

        document.getElementById("score_container").style= "font-weight: 400;"
        let section = document.getElementById("tech");
        if (section) {
            section.style.height = "auto"; // Set height to auto
        }
    });
}

