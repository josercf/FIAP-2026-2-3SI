// Java (Spring) Example
public interface FreightStrategy {
    double calculate(double distance);
}

public class SedexStrategy implements FreightStrategy {
    public double calculate(double distance) {
        return distance * 1.5;
    }
}
