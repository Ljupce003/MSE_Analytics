package org.example.dians.Component;

import lombok.Getter;
import lombok.Setter;
import org.springframework.stereotype.Component;

@Setter
@Getter
@Component
public class PythonRunnerFlag {
    public PythonRunnerFlag() {
        flag = false;
        analysis_flag=false;
        lstm_flag=false;
    }

    public static boolean flag;
    public static boolean analysis_flag;
    public static boolean lstm_flag;

}
