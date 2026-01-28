"use client";

import { useState } from "react";
import { UserPlus, Copy, Check } from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/lib/hooks";

interface SignUpModalProps {
  open: boolean;
  onClose: () => void;
  onSwitchToSignIn: () => void;
}

/**
 * Sign Up Modal component matching GIM.pen design (iAl8m).
 */
export function SignUpModal({ open, onClose, onSwitchToSignIn }: SignUpModalProps) {
  const [generatedId, setGeneratedId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [description, setDescription] = useState("");
  const { createGimIdAsync, signIn, isLoading, error } = useAuth();

  const handleGenerate = async () => {
    try {
      const result = await createGimIdAsync({ description: description || undefined });
      setGeneratedId(result.gim_id);
    } catch {
      // Error is handled by the hook
    }
  };

  const handleCopy = async () => {
    if (generatedId) {
      await navigator.clipboard.writeText(generatedId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleContinue = () => {
    if (generatedId) {
      signIn(generatedId, {
        onSuccess: () => {
          onClose();
          setGeneratedId(null);
          setDescription("");
        },
      });
    }
  };

  const handleClose = () => {
    onClose();
    setGeneratedId(null);
    setDescription("");
    setCopied(false);
  };

  return (
    <Modal open={open} onClose={handleClose}>
      <ModalHeader onClose={handleClose}>
        <ModalTitle>Create Your GIM ID</ModalTitle>
      </ModalHeader>

      <ModalContent>
        <Tabs defaultValue="signup">
          <TabsList className="w-full">
            <TabsTrigger
              value="signin"
              className="flex-1"
              onClick={onSwitchToSignIn}
            >
              Sign In
            </TabsTrigger>
            <TabsTrigger value="signup" className="flex-1">Sign Up</TabsTrigger>
          </TabsList>
        </Tabs>

        <p className="text-sm text-text-secondary">
          Create your GIM ID to start tracking issues and contributing to the global memory.
        </p>

        {!generatedId ? (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="description" className="text-sm font-medium text-text-primary">
                Description (optional)
              </label>
              <Input
                id="description"
                type="text"
                placeholder="My development machine"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isLoading}
              />
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            <ModalFooter>
              <Button
                type="button"
                className="w-full"
                onClick={handleGenerate}
                disabled={isLoading}
              >
                <UserPlus className="h-4 w-4" />
                {isLoading ? "Generating..." : "Generate GIM ID"}
              </Button>
            </ModalFooter>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-text-primary">
                Your GIM ID
              </label>
              <div className="relative">
                <Input
                  type="text"
                  value={generatedId}
                  readOnly
                  className="pr-12 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={handleCopy}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-success-foreground" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-warning-foreground bg-warning p-2 rounded-lg">
                Save this ID! You&apos;ll need it to sign in later. We cannot recover it for you.
              </p>
            </div>

            <ModalFooter>
              <Button
                type="button"
                className="w-full"
                onClick={handleContinue}
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Continue to Dashboard"}
              </Button>
            </ModalFooter>
          </div>
        )}

        <p className="text-center text-xs text-text-muted">
          Already have an ID?{" "}
          <button
            type="button"
            onClick={onSwitchToSignIn}
            className="text-primary underline hover:no-underline"
          >
            Sign in
          </button>
        </p>
      </ModalContent>
    </Modal>
  );
}
