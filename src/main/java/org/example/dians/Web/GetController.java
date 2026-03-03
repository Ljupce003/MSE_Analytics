package org.example.dians.Web;

import org.example.dians.Component.PythonRunnerFlag;
import org.example.dians.Scraping.CSVtoJAVA;
import org.example.dians.Scraping.PythonScriptRunner;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Controller

public class GetController {
    public GetController() {
        PythonScriptRunner.runPythonScript();
        PythonScriptRunner.runPythonScriptFundamentalAnalysis();
        PythonScriptRunner.runPythonScriptLSTM();
    }

    @GetMapping("/scr")
    public String showScrPage(Model model) {
        PythonScriptRunner.runPythonScript();
        return "index";
    }

    @GetMapping(path = {"/index","/"})
    public String showIndexPage(Model model) {
        if(PythonRunnerFlag.flag){
            model.addAttribute("error","Fetching data...");
        }
        System.out.println(PythonRunnerFlag.flag);

        return "index";
    }

    @GetMapping("/tech_analysis")
    public String showTechPage(Model model) {

        if(PythonRunnerFlag.flag){
            model.addAttribute("error","Fetching data...");
        }
        return "tech_analysis";
    }

    @GetMapping("/fundamental")
    public String showFundamentalPage(Model model) {
        if(PythonRunnerFlag.flag){
            model.addAttribute("error","Fetching data...");
        }
        if(PythonRunnerFlag.analysis_flag){
            model.addAttribute("analysis_error","Fundamental Analysis is not finished");
        }
        List<String> list = new ArrayList<>(CSVtoJAVA.AnalysisCodes().keySet());

        model.addAttribute("codes_dropdown",list.stream().sorted().collect(Collectors.toList()));
        return "fundamental";
    }

    @GetMapping("/lstm")
    public String showLstmPage(Model model) {
        if(PythonRunnerFlag.flag){
            model.addAttribute("error","Fetching data...");
        }
        return "lstm";
    }
}
