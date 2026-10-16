# Architecture and coding standards (REPLACE WITH YOUR OWN)

Gates 2 and 4 judge work against this file. The examples below are
placeholders. An agent reviewing against vague standards gives vague
verdicts, so make each rule specific and checkable.

## 1. Triggers

1.1 One trigger per object. Logic lives in a handler class.
1.2 Use the team's trigger framework: <name it here>.

## 2. Apex

2.1 Every class declares `with sharing`, `without sharing`, or `inherited sharing`. `without sharing` requires a comment explaining why.
2.2 SOQL in user-facing code runs `WITH USER_MODE` or uses `Security.stripInaccessible`.
2.3 No SOQL, DML, or callouts inside loops.
2.4 No hard-coded record IDs or URLs. Use Custom Metadata or Custom Settings.

## 3. Integrations

3.1 All callouts use Named Credentials.
3.2 Every callout has a timeout, error handling, and a logged failure path.

## 4. Data model

4.1 Field API names: <your convention>.
4.2 New objects need a stated owner and a data retention note.

## 5. Approved tools

5.1 Flows for <cases>; Apex for <cases>.
