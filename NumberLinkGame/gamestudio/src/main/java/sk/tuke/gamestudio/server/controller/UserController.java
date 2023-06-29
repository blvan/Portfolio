package sk.tuke.gamestudio.server.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.context.WebApplicationContext;
import sk.tuke.gamestudio.entity.Users;
import sk.tuke.gamestudio.service.UsersService;

import java.util.List;
import java.util.Objects;

@Controller
@Scope(WebApplicationContext.SCOPE_SESSION)
public class UserController {

    private Users loggedUser;
    @Autowired
    private UsersService usersService;

    @PostMapping("/login")
    public String login(String login, String password) {
        if ("heslo".equals(password)) {
            loggedUser = new Users(login, password);
            usersService.addUser(loggedUser);
            return "redirect:/numberlink";
        }
        return "redirect:/";
    }


    @GetMapping("/logout")
    public String logout() {
        loggedUser = null;
        return "redirect:/";
    }

    public Users getLoggedUser() {
        return loggedUser;
    }

    public boolean isLogged() {
        return loggedUser != null;
    }
}
