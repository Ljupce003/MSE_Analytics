package org.example.dians.Web;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ProgressPageController {

    @GetMapping("/progress")
    public String progressPage() {
        return "progress";
    }

}
