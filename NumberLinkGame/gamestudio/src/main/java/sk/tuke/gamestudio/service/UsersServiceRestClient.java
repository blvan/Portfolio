package sk.tuke.gamestudio.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.client.RestTemplate;
import sk.tuke.gamestudio.entity.Users;

import java.util.Arrays;
import java.util.List;
import java.util.Objects;

public class UsersServiceRestClient implements UsersService {
    private final String url = "http://localhost:8080/api/users";

    @Autowired
    private RestTemplate restTemplate;


    @Override
    public void addUser(Users users) throws UsersException {
        restTemplate.postForEntity(url, users, Users.class);
    }

    @Override
    public List<Users> getUsers() throws UsersException {
        return Arrays.asList(Objects.requireNonNull(restTemplate.getForEntity(url, Users[].class).getBody()));
    }
}
