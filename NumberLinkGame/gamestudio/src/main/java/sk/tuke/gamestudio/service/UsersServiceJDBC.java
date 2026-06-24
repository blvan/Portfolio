package sk.tuke.gamestudio.service;

import sk.tuke.gamestudio.entity.Users;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class UsersServiceJDBC implements UsersService {
    public static final String URL = "jdbc:postgresql://dbs.kpi.fei.tuke.sk:5432/ivandemchenko";
    public static final String USER = "ivandemchenko";
    public static final String PASSWORD = "kwfhSG6%";
    public static final String SELECT = "SELECT login, password FROM users ORDER BY login";
    public static final String INSERT = "INSERT INTO users(login, password) values (?,?)";

    @Override
    public void addUser(Users users) throws UsersException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement statement = connection.prepareStatement(INSERT)
        ) {
            statement.setString(1, users.getLogin());
            statement.setString(2, users.getPassword());
            statement.executeUpdate();
        } catch (SQLException e) {
            throw new UsersException("Problem inserting user", e);
        }
    }

    @Override
    public List<Users> getUsers() throws UsersException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement statement = connection.prepareStatement(SELECT)
        ) {
            try (ResultSet rs = statement.executeQuery()) {
                List<Users> users = new ArrayList<>();
                while (rs.next()) {
                    users.add(new Users(rs.getString(1), rs.getString(2)));
                }
                return users;
            }
        } catch (SQLException e) {
            throw new UsersException("Problem selecting comment", e);
        }
    }
}
