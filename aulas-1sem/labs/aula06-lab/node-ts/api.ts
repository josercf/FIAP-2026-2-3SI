// TypeScript Adapter Pattern stub
class LegacySystem {
    public specificRequest(): string {
        return ".tseuqer cificeps eht si sihT";
    }
}

class Adapter {
    private adaptee: LegacySystem;
    constructor(adaptee: LegacySystem) {
        this.adaptee = adaptee;
    }
    public request(): string {
        const result = this.adaptee.specificRequest().split('').reverse().join('');
        return `Adapter: (TRANSLATED) ${result}`;
    }
}
