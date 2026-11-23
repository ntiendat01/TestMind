//! Locator field types shared with the Python reference.

use std::collections::BTreeMap;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum LocValue {
    Number(i64),
    Text(String),
}

pub type Loc = BTreeMap<String, LocValue>;

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct RowFields(pub BTreeMap<String, Option<String>>);

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct TableData {
    pub header: Vec<String>,
    pub rows: Vec<Vec<String>>,
}
