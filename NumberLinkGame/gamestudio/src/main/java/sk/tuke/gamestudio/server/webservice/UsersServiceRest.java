package sk.tuke.gamestudio.server.webservice;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import sk.tuke.gamestudio.entity.Users;
import sk.tuke.gamestudio.service.UsersService;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UsersServiceRest {
    @Autowired
    private UsersService usersService;

    @GetMapping
    public List<Users> getUsers() {
        return usersService.getUsers();
    }

    @PostMapping
    public void addComment(@RequestBody Users users) {
        usersService.addUser(users);
    }
}
