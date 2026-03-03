fetch("/download/mega-data.csv")
    .then((response) => response.text())
    .then((csvData) => {
        const parsedData = parseCSV(csvData);
        initializeChart(parsedData);
    })
    .catch((error) => console.error("Error loading CSV:", error));

function parseCSV(csv) {
    const rows = csv.split("\n");
    const stockData = {};

    rows.forEach((row, index) => {
        if (index === 0 || row.trim() === "") return; // Skip header or empty rows
        const fields = row.split(",");

        const stockCode = fields[0];
        let date = fields[1];
        const close = parseFloat(fields[2]);
        const max = parseFloat(fields[3]);
        const low = parseFloat(fields[4]);
        const avg = parseFloat(fields[5]);
        const volume = parseFloat(fields[6]);
        const turnover = parseFloat(fields[7]);

        // Convert the date from DD.MM.YYYY to YYYY-MM-DD format
        const [day, month, year] = date.split(".");
        date = `${year}-${month}-${day}`; // Reformat to YYYY-MM-DD

        if (!stockData[stockCode]) {
            stockData[stockCode] = [];
        }

        if (close !== null && max !== null && avg !== null && volume !== null) {
            stockData[stockCode].push([date, close, max, low, avg, volume, turnover]);
        }
    });

    return stockData;
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
            { top: "80%", height: "20%" },
        ],

        tooltip: {
            pointFormatter: function () {
                return (
                    "<b>" +
                    this.series.name +
                    "</b><br>" +
                    "Price: " +
                    Highcharts.numberFormat(this.y, 2, ",", ".") +
                    "<br>" +
                    "Date: " +
                    Highcharts.dateFormat("%e %b %Y", this.x)
                ); // Format the date as well
            },
        },

        series: [
            {
                type: "candlestick",
                id: stockCode,
                name: stockCode,
                data: formatStockData(stockData[stockCode]),
            },
            {
                type: "column",
                id: "volume",
                name: "Volume",
                data: formatVolumeData(stockData[stockCode]),
                yAxis: 1,
            },
        ],
    });

    stockSelector.addEventListener("change", function () {
        const selectedStock = stockSelector.value;
        chart.series[0].setData(formatStockData(stockData[selectedStock]));
        chart.series[1].setData(formatVolumeData(stockData[selectedStock]));
        chart.setTitle({ text: selectedStock + " Historical" });

        chart.update({
            tooltip: {
                pointFormatter: function () {
                    return (
                        "<b>" +
                        selectedStock +
                        "</b><br>" +
                        "Price: " +
                        Highcharts.numberFormat(this.y, 2, ",", ".") +
                        "<br>" +
                        "Date: " +
                        Highcharts.dateFormat("%e %b %Y", this.x)
                    );
                },
            },
        });
    });

    document.getElementById("overlays").addEventListener("change", function () {
        const selectedOverlay = this.value;
        const overlaySeries = chart.get("overlay");
        if (overlaySeries) overlaySeries.remove();
        chart.addSeries({
            type: selectedOverlay,
            id: "overlay",
            linkedTo: stockCode,
        });
    });

    document
        .getElementById("oscillators")
        .addEventListener("change", function () {
            const selectedOscillator = this.value;
            const oscillatorSeries = chart.get("oscillator");
            if (oscillatorSeries) oscillatorSeries.remove();
            chart.addSeries({
                type: selectedOscillator,
                id: "oscillator",
                linkedTo: stockCode,
                yAxis: 2,
            });
        });
}

function formatStockData(stockData) {
    return stockData.map((item) => {
        const date = item[0]; // date is already in YYYY-MM-DD format
        return [
            new Date(date).getTime(), // Convert the date to a valid timestamp
            item[1], // close
            item[2], // max
            item[3] !== null ? item[3] : 0, // low
            item[4], // avg
        ];
    });
}

function formatVolumeData(stockData) {
    return stockData.map((item) => [new Date(item[0]).getTime(), item[5]]);
}


















//
// function parsePrice(priceStr) {
//     // Replace commas with periods and remove non-numeric characters
//     priceStr = priceStr.replace(".", "").replace(",", ".");
//     return parseFloat(priceStr);
// }
//
// function filterDataByStockCode(data) {
//     let previousClose = null; // За следење на затворањето на претходниот ред
//
//     return data.map((row, index) => {
//         const date = row[1];
//         const open = parsePrice(row[2]); // Тековното затворање е `row[2]`
//         let close;
//
//         // Ако е првиот ред, постави почетната цена со default offset
//         if (index === 0) {
//             close = parsePrice(row[4]);
//         } else {
//             close = previousClose; // Почетната цена е затворањето на претходниот ред
//         }
//
//         const high = parsePrice(row[3]);
//         const low = parsePrice(row[4]);
//
//         // Конвертирај го датумот во валиден JavaScript датум
//         const dateParts = date.split(".");
//         const validDate = new Date(
//             parseInt(dateParts[2]), // Година
//             parseInt(dateParts[1]) - 1, // Месец (0-базиран индекс)
//             parseInt(dateParts[0]) // Ден
//         );
//
//         // Ажурирај ја затворачката цена за следниот ред
//         previousClose = open;
//
//         return {
//             x: validDate,
//             y: [open, high, low, close], // Open, High, Low, Close
//         };
//     });
// }
//
//
//
//
// // Function to render the candlestick chart using CanvasJS
// function renderChart(chartData) {
//   const chart = new CanvasJS.Chart("chartContainer", {
//     animationEnabled: true,
//     theme: "light2", // Using a light theme to avoid dark blue color
//     zoomEnabled: true,
//     exportEnabled: true,
//     axisX: {
//       title: "Date",
//       valueFormatString: "DD MMM YYYY",
//       gridColor: "#313748",
//       labelFontColor: "#9a9ea3",
//       titleFontColor: "#ffffff",
//     },
//     axisY: {
//       gridColor: "#313748",
//       labelFontColor: "#9a9ea3",
//       titleFontColor: "#ffffff",
//       title: "Price",
//       prefix: "MKD ",
//       labelFormatter: function (e) {
//         // Format Y-axis labels as "16.750,00"
//         return formatCurrency(e.value);
//       },
//     },
//     data: [
//       {
//         type: "candlestick",
//         risingColor: "#339c90",
//         fallingColor: "#ff1a00",
//         yValueFormatString: "MKD #,##0.00", // Default formatting
//         dataPoints: chartData,
//       },
//     ],
//   });
//
//   changeBorderColor(chart);
//   chart.render();
// }
//
// // Helper function to format numbers as "16.750,00" (with periods as thousand separators and commas as decimal separator)
// function formatCurrency(value) {
//   return value.toLocaleString("de-DE", {
//     minimumFractionDigits: 2,
//     maximumFractionDigits: 2,
//   });
// }
//
// // Function to change border color
// function changeBorderColor(chart) {
//   var dataSeries;
//   for (var i = 0; i < chart.options.data.length; i++) {
//     dataSeries = chart.options.data[i];
//     for (var j = 0; j < dataSeries.dataPoints.length; j++) {
//       dataSeries.dataPoints[j].color =
//         dataSeries.dataPoints[j].y[0] <= dataSeries.dataPoints[j].y[3]
//           ? dataSeries.risingColor
//             ? dataSeries.risingColor
//             : dataSeries.color
//           : dataSeries.fallingColor
//           ? dataSeries.fallingColor
//           : dataSeries.color;
//     }
//   }
// }
