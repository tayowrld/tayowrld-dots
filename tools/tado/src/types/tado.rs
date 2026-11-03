use chrono::NaiveDate;

pub(crate) struct Tado {
    pub(crate) id: u32,
    pub(crate) title: String,
    pub(crate) is_done: bool,
    pub(crate) date: NaiveDate
}

pub(crate) struct App {
    pub(crate) todo: Vec<Tado>,
}

