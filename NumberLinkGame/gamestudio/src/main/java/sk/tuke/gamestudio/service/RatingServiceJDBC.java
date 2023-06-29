package sk.tuke.gamestudio.service;


import sk.tuke.gamestudio.entity.Rating;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;


public class RatingServiceJDBC implements RatingService {
    public static final String URL = "jdbc:postgresql://dbs.kpi.fei.tuke.sk:5432/ivandemchenko";
    public static final String USER = "ivandemchenko";
    public static final String PASSWORD = "kwfhSG6%";
    public static final String SELECT = "SELECT game, player, rating, ratedOn FROM rating WHERE game = ? ORDER BY ratedOn DESC LIMIT 5";
    public static final String SELECT_AVG = "SELECT AVG(rating) FROM rating WHERE game = ? ";
    public static final String DELETE = "DELETE FROM rating";
    public static final String INSERT = "INSERT INTO rating (game, player, rating, ratedOn) VALUES (?, ?, ?, ?)";
    @Override
    public void setRating(Rating rating) throws RatingException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement statement = connection.prepareStatement(INSERT)
        ) {
            statement.setString(1, rating.getPlayer());
            statement.setString(2, rating.getGame());
            statement.setInt(3, rating.getRating());
            statement.executeUpdate();
        } catch (SQLException e) {
            throw new ScoreException("Problem inserting rating", e);
        }
    }

    @Override
    public int getAverageRating(String game) throws RatingException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement statement = connection.prepareStatement(SELECT_AVG);
        ) {
            statement.setString(1, game);
            try (ResultSet rs = statement.executeQuery()) {
                int averageRating = 0;
                while ( rs.next() ) {
                    averageRating = rs.getInt("avg");
                }

                return averageRating;
            }
        } catch (SQLException e) {
            throw new ScoreException("Problem selecting rating", e);
        }
    }

    @Override
    public int getRating(String game, String player) throws RatingException {
        return 0;
    }
    @Override
    public List<Rating> getRatings(String game) throws RatingException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement statement = connection.prepareStatement(SELECT);
        ) {
            statement.setString(1, game);
            try (ResultSet rs = statement.executeQuery()) {
                List<Rating> ratings = new ArrayList<>();
                while (rs.next()) {
                    ratings.add(new Rating(rs.getString(2), rs.getString(1), rs.getInt(3)));
                }
                return ratings;
            }
        } catch (SQLException e) {
            throw new ScoreException("Problem selecting rating", e);
        }
    }

    @Override
    public void reset() throws RatingException {
        try (Connection connection = DriverManager.getConnection(URL, USER, PASSWORD);
             Statement statement = connection.createStatement();
        ) {
            statement.executeUpdate(DELETE);
        } catch (SQLException e) {
            throw new ScoreException("Problem deleting rating", e);
        }
    }
}