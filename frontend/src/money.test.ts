import { centsToInput, computeFee, formatEuro, parseEuroToCents } from "./money";

describe("parseEuroToCents", () => {
  it("accepts comma and dot decimals", () => {
    expect(parseEuroToCents("10")).toBe(1000);
    expect(parseEuroToCents("10,5")).toBe(1050);
    expect(parseEuroToCents("10.50")).toBe(1050);
    expect(parseEuroToCents(" 0,99 ")).toBe(99);
  });

  it("avoids floating point errors", () => {
    expect(parseEuroToCents("1,15")).toBe(115);
    expect(parseEuroToCents("19,99")).toBe(1999);
  });

  it("rejects invalid amounts", () => {
    expect(parseEuroToCents("")).toBeNull();
    expect(parseEuroToCents("-1")).toBeNull();
    expect(parseEuroToCents("1,234")).toBeNull();
    expect(parseEuroToCents("abc")).toBeNull();
  });
});

describe("formatting", () => {
  it("formats cents as euro", () => {
    expect(formatEuro(1300).replace(/\s/g, " ")).toBe("13,00 €");
  });

  it("formats cents for an input field", () => {
    expect(centsToInput(1050)).toBe("10,50");
  });
});

describe("computeFee", () => {
  it("adds the per-day amount for each day", () => {
    expect(computeFee(3, 1000, 100)).toBe(1300);
  });

  it("charges only the base fee with no days", () => {
    expect(computeFee(0, 1000, 100)).toBe(1000);
  });
});
