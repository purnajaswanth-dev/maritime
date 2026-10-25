package com.whereismyferry.backend.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class SpaWebController {

    /**
     * Forwards browser navigation routes to the React single page application entrypoint.
     * Spring Boot serves the prebuilt frontend from classpath:/static/index.html.
     */
    @GetMapping(value = {
            "/",
            "/timetable",
            "/timetable/**",
            "/ports",
            "/ports/**",
            "/routes",
            "/routes/**",
            "/fares",
            "/fares/**",
            "/bookings",
            "/bookings/**",
            "/tracking",
            "/tracking/**",
            "/track",
            "/track/**",
            "/login",
            "/register",
            "/admin",
            "/admin/**",
            "/unauthorized"
    })
    public String forwardSpa() {
        return "forward:/index.html";
    }
}
