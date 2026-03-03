package org.example.dians.Scraping;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.opencsv.CSVReader;
import com.opencsv.exceptions.CsvValidationException;
import org.example.dians.model.Issuer;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@Service
public class CSVtoJAVA {

//

    public static List<List<Object>> Filter_Code(String cod) {
        String filePath = System.getProperty("user.dir") + "/Domasna3/dians/src/main/python/Smestuvanje/mega-data.csv";  //TODO Voa treba se smene ako frla error file not found
        List<List<Object>> csvData = new ArrayList<>();

        // Ако "cod" е празен, врати празен список
        if (cod.equals("")) {
            return csvData;
        }

        try (CSVReader reader = new CSVReader(new FileReader(filePath))) {
            String[] line;

            // Прочитај го секој ред од CSV фајлот
            while ((line = reader.readNext()) != null) {
                if (line.length > 0 && line[0].trim().equals(cod)) {
                    List<Object> row = new ArrayList<>();

                    // Додај ги податоците во row според нивната позиција
                    row.add(line[0].trim()); // Код
                    row.add(line[1].trim()); // Датум

                    row.add(line[2].replace("\"", "").trim()); // Отворање
                    row.add(line[3].replace("\"", "").trim()); // Макс
                    row.add(line[4].replace("\"", "").trim()); // Мин
                    row.add(line[5].replace("\"", "").trim()); // Затворање
                    row.add(line[6].trim()); // Промена

                    // Раздвој ги количините ако постојат
                    if (line.length > 7) {
                        String[] quantities = line[7].split(",");
                        for (String qty : quantities) {
                            row.add(qty.trim());
                        }
                    }

                    // Додај ја обработената линија во резултатот
                    csvData.add(row);
                }
            }
        } catch (IOException | CsvValidationException e) {
            e.printStackTrace();
        }

        return csvData;
    }
    public static void print(List<List<Object>> csvData){
        // Испечатете ги податоците
        for (List<Object> rowData : csvData) {
            System.out.println(rowData);
        }
    }
    public static Map<String, String> Codes_for_Dropdown(){

        // Патека до JSON фајлот
        String filePath = System.getProperty("user.dir") + "/src/main/python/Smestuvanje/names.json";   //TODO Voa treba se smene ako frla error file not found

        // Креирај ObjectMapper
        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, String> hvMap = new HashMap<>();


        try {
            // Читање на JSON како општа листа
            List<?> jsonData = objectMapper.readValue(new File(filePath), List.class);

            // Претворање во мапа
            for (Object obj : jsonData) {
                Map<?, ?> record = (Map<?, ?>) obj; // Кастирање на секој објект во мапа
                String key = (String) record.get("Issuer code");
                String value = (String) record.get("Issuer name");
                hvMap.put(key, value);
            }

        } catch (IOException e) {
            System.err.println("Грешка при читање на JSON фајлот: " + e.getMessage());
        }

        return hvMap;
    }

    public static Map<String, String> AnalysisCodes(){

        // Патека до JSON фајлот
        String filePath = System.getProperty("user.dir") + "/src/main/python/Smestuvanje/channels.json"; //TODO Voa treba se smene ako frla error file not found

        // Креирај ObjectMapper
        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, String> hvMap = new HashMap<>();


        try {
            // Читање на JSON како општа листа
            List<?> jsonData = objectMapper.readValue(new File(filePath), List.class);

            // Претворање во мапа
            for (Object obj : jsonData) {
                Map<?, ?> record = (Map<?, ?>) obj; // Кастирање на секој објект во мапа
                String key = (String) record.get("code");
                String value = (String) record.get("title");
                hvMap.put(key, value);
            }

        } catch (IOException e) {
            System.err.println("Грешка при читање на JSON фајлот за Фундаментална Анализа: " + e.getMessage());
            System.err.println("Current Workdir is "+System.getProperty("user.dir"));

        }

        return hvMap;
    }

    public static Issuer GetAnalysisResultByCode(String code){
        try {
            String filePath = System.getProperty("user.dir") + "/src/main/python/Smestuvanje/channels.json"; //TODO Voa treba se smene ako frla error file not found
            // Parse JSON file
            ObjectMapper mapper = new ObjectMapper();
            Issuer[] dataArray = mapper.readValue(new File(filePath), Issuer[].class);

            // Filter by code

            Issuer returnIssuer=null;
            for (Issuer data : dataArray) {
                if (data.getCode().equals(code)) {
                    returnIssuer=data;
                    break;
                }
            }
            return returnIssuer;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }


    public static  List<List<Object>> Filter_Data( List<List<Object>> list,Date from,Date to ){
        if(from==null || to==null){
            return list;
        }

        List<List<Object>> novaData = new ArrayList<>();
        for (List<Object> rowData : list) {
            String parsData= rowData.get(1).toString();

            Date date = new Date(0,0,0);
            // Форматот на датумот
            SimpleDateFormat dateFormat = new SimpleDateFormat("d.M.yyyy");

            try {
                // Парсирање на датумот
                date = dateFormat.parse(parsData);

                // Испечати го резултатот
//                System.out.println("Parsed date: " + date);
            } catch (ParseException e) {
                e.printStackTrace();
            }

            if(date.before(from) && date.after(to)){

                novaData.add(rowData);
            }

        }
        return novaData;
    }
}
