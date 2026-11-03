use chrono::{Utc,Duration,NaiveDate};


pub fn parse_date(date: String) -> NaiveDate {
    match date.as_str() {
        "today" | "n" => Utc::now().date_naive(),
        "yesterday" | "y" => Utc::now().date_naive() - Duration::days(1),
        "tomorrow" | "t" => Utc::now().date_naive() + Duration::days(1),
        &_ => date.parse::<NaiveDate>().expect("Not a date")
    }
}

