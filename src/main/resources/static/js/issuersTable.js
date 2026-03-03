var jsonPath = "/download/names.json";

window.onload = function () {
    fetch(jsonPath)
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Проблем со вчитување: " + response.statusText);
            }
            return response.json();
        })
        .then(function (jsonData) {
            if (!Array.isArray(jsonData) || jsonData.length === 0) {
                document.getElementById("tableContainer").innerHTML =
                    "<div class='p-8 text-center text-gray-500 italic'>Нема достапни податоци за издавачите.</div>";
                return;
            }

            var tableContainer = document.getElementById("tableContainer");
            tableContainer.innerHTML = "";

            // Креирање на обвивка за респонзивност
            var wrapper = document.createElement("div");
            wrapper.className = "overflow-x-auto custom-scrollbar";

            var table = document.createElement("table");
            table.className = "min-w-full divide-y divide-gray-200";

            var thead = document.createElement("thead");
            thead.className = "bg-gray-50 sticky top-0";

            var tbody = document.createElement("tbody");
            tbody.className = "bg-white divide-y divide-gray-100";

            // Генерација на наслови (Headers)
            var headers = Object.keys(jsonData[0]);
            var headerRow = document.createElement("tr");
            headers.forEach(function (header) {
                var th = document.createElement("th");
                th.className = "px-6 py-4 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest";
                th.textContent = header;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            // Генерација на редови (Rows)
            jsonData.forEach(function (item, index) {
                var row = document.createElement("tr");
                // Додавање на hover ефект и менување на боја на секој втор ред (zebra striping)
                row.className = "hover:bg-blue-50/50 transition-colors duration-150 group cursor-pointer";

                headers.forEach(function (header) {
                    var cell = document.createElement("td");
                    cell.className = "px-6 py-4 text-sm text-gray-700 font-medium";
                    // console.log(header)

                    // Специјално стилизирање ако е колона со Шифра/Код
                    if (header.toLowerCase().includes('code')) {
                        cell.innerHTML = `<span class="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs font-bold border border-gray-200 group-hover:border-blue-200 group-hover:bg-blue-100 transition-colors">${item[header]}</span>`;
                    } else if(header.toLowerCase().includes('link')){
                        if (item[header]) {
                            cell.innerHTML = `
                <a href="${item[header]}" 
                   target="_blank" 
                   class="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline transition-colors gap-1.5 font-semibold">
                    Посети <i class="fas fa-external-link-alt text-[10px]"></i>
                </a>`;
                        } else {
                            cell.innerHTML = `<span class="text-gray-400 italic text-xs">Нема линк</span>`;
                        }
                    }
                    else {
                        cell.textContent = item[header] || "";
                    }

                    row.appendChild(cell);
                });
                tbody.appendChild(row);
            });

            table.appendChild(thead);
            table.appendChild(tbody);
            wrapper.appendChild(table);
            tableContainer.appendChild(wrapper);
        })
        .catch(function (error) {
            document.getElementById("tableContainer").innerHTML =
                `<div class="p-6 bg-red-50 text-red-600 border border-red-100 rounded-lg mx-4 my-4 flex items-center gap-3">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Грешка: ${error.message}</span>
                </div>`;
        });
};