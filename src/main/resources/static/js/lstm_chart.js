
let csvMega = null
let csvLSTM =null;

fetch("/download/mega-data.csv")
    .then((response) => response.text())
    .then((csvMData) => {
        csvMega=csvMData

    })
    .catch((error) => console.error("Error loading Mega-data CSV:", error));

fetch("/download/processed_lstm.csv")
    .then((response) => response.text())
    .then((csvLSTMData) => {
        csvLSTM=csvLSTMData
    })
    .catch((error) => console.error("Error loading CSV:", error));


var parsedLSTM_data=parseLSTM_CSV(csvLSTM)
var parsedMegadata=parseMegaCSV(csvMega)

function parseLSTM_CSV(csv) {
    const rows = csv.split("\n");
    const return_lstm_json = {};

    rows.forEach((row, index) => {
        if (index === 0 || row.trim() === "") return; // Skip header or empty rows
        const fields = row.split(",");

        const stockCode = fields[3];
        let date = fields[0];
        const close = parseFloat(fields[2]);
        let score = parseFloat(fields[4])


        // Convert the date from DD.MM.YYYY to YYYY-MM-DD format
        const [day, month, year] = date.split(".");
        date = `${year}-${month}-${day}`; // Reformat to YYYY-MM-DD

        if (!return_lstm_json[stockCode]) {
            return_lstm_json[stockCode] = [];
        }

        if (close !== null) {
            return_lstm_json[stockCode].push([date, close,score]);
        }
    });

    return return_lstm_json;
}


function parseMegaCSV(csv) {
    const rows = csv.split("\n");
    const return_json = {};

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

        if (!return_json[stockCode]) {
            return_json[stockCode] = [];
        }

        if (close !== null && max !== null && avg !== null && volume !== null) {
            return_json[stockCode].push([date, close, max, low, avg, volume, turnover]);
        }
    });

    return return_json;
}




function initializeChartLSTM(stockData) {
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


function mergeData(lstmData, megaData) {
    const mergedData = {};
    const lstmKeys = Object.keys(lstmData);

    let score = null

    lstmKeys.forEach((stockCode) => {
        const lstmEntries = lstmData[stockCode];
        const megaEntries = megaData[stockCode];

        if (!megaEntries) return; // Skip if no matching stock in mega data

        const megaMap = new Map(
            megaEntries.map(([date, close]) => [date, close])
        );

        if (!mergedData[stockCode]) {
            mergedData[stockCode] = [];
        }

        lstmEntries.forEach(([date, close]) => {
            if (megaMap.has(date)) {
                mergedData[stockCode].push({
                    date: date,
                    lstmClose: close,
                    megaClose: megaMap.get(date),
                });
            }
        });
    });

    return mergedData;
}

var parsedLSTM_data=parseLSTM_CSV(csvLSTM)
var parsedMegadata=parseMegaCSV(csvMega)
mergeData(parsedLSTM_data,parsedMegadata)









